"""核心引擎：把「自然语言问题」变成「跑出来的答案 + 图」。

流程：
  读数据 → 提取 schema → 让 LLM 写 pandas 代码 → 受限执行 → 出错就让 LLM 改 → 返回结果

安全说明：本工具会执行 LLM 生成的代码。虽然做了基础防护（禁用危险内置函数、
静态扫描危险关键字），但**请只在可信数据上使用**，生产环境建议放进沙箱/容器。
"""

from __future__ import annotations

import io
import os
import re
from contextlib import redirect_stdout
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .llm import LLMClient
from .prompts import SYSTEM_PROMPT, build_fix_message, build_user_message

# 静态扫描：出现这些就直接拒绝执行，挡掉最明显的越权操作
_FORBIDDEN = re.compile(
    r"\b(import\s+os|import\s+sys|import\s+subprocess|__import__|"
    r"\bopen\s*\(|eval\s*\(|exec\s*\(|os\.|sys\.|subprocess|socket|"
    r"requests|urllib|shutil|pathlib|globals\(|locals\()",
)

_CODE_BLOCK = re.compile(r"```(?:python)?\s*\n(.*?)```", re.DOTALL)


def load_data(path: str, **read_kwargs) -> pd.DataFrame:
    ext = os.path.splitext(path)[1].lower()
    if ext in (".csv",):
        return pd.read_csv(path, **read_kwargs)
    if ext in (".tsv", ".txt"):
        read_kwargs.setdefault("sep", "\t")
        return pd.read_csv(path, **read_kwargs)
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path, **read_kwargs)
    if ext in (".parquet",):
        return pd.read_parquet(path, **read_kwargs)
    if ext in (".json",):
        return pd.read_json(path, **read_kwargs)
    raise ValueError(f"暂不支持的文件格式：{ext}")


def describe_schema(df: pd.DataFrame, sample_rows: int = 3) -> str:
    """生成给 LLM 看的紧凑 schema：列名、类型、几行样例。"""
    lines = [f"共 {len(df)} 行 {df.shape[1]} 列。", "列（名称 : 类型）："]
    for col in df.columns:
        lines.append(f"  - {col} : {df[col].dtype}")
    try:
        sample = df.head(sample_rows).to_dict(orient="records")
        lines.append(f"前 {sample_rows} 行样例：{sample}")
    except Exception:  # pragma: no cover - 极端类型转 dict 失败时跳过
        pass
    return "\n".join(lines)


def extract_code(text: str) -> str:
    """从 LLM 回复里抠出 python 代码块；没有围栏就退回整段。"""
    m = _CODE_BLOCK.search(text)
    return (m.group(1) if m else text).strip()


def _safe_globals(df: pd.DataFrame) -> dict:
    # 只暴露数据分析需要的东西，并给一个最小化的 builtins
    safe_builtins = {
        k: __builtins__[k] if isinstance(__builtins__, dict) else getattr(__builtins__, k)
        for k in (
            "abs", "min", "max", "sum", "len", "range", "round", "sorted",
            "list", "dict", "set", "tuple", "str", "int", "float", "bool",
            "enumerate", "zip", "map", "filter", "print", "type", "isinstance",
        )
    }
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    try:
        plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "Arial Unicode MS"]
        plt.rcParams["axes.unicode_minus"] = False
    except Exception:  # pragma: no cover
        pass

    return {
        "__builtins__": safe_builtins,
        "df": df,
        "pd": pd,
        "np": np,
        "plt": plt,
    }


@dataclass
class RunResult:
    answer: str  # 代码 print 出来的内容（给用户看的结论）
    code: str  # 最终成功执行的代码
    chart_path: str | None = None  # 若画了图，保存的路径
    attempts: int = 1  # 实际尝试次数（含纠错重试）
    history: list = field(default_factory=list)


def _execute(code: str, df: pd.DataFrame, chart_path: str) -> tuple[str, str | None]:
    """受限执行代码，返回 (stdout, 图片路径或 None)。出错则抛异常。"""
    if _FORBIDDEN.search(code):
        raise ValueError("生成的代码包含被禁止的操作（文件/网络/系统调用），已拦截。")

    g = _safe_globals(df)
    plt = g["plt"]
    plt.close("all")

    buf = io.StringIO()
    with redirect_stdout(buf):
        exec(compile(code, "<askcsv-generated>", "exec"), g)  # noqa: S102 - 见模块安全说明

    saved = None
    if plt.get_fignums():  # 代码画了图
        plt.savefig(chart_path, dpi=130, bbox_inches="tight")
        plt.close("all")
        saved = chart_path
    return buf.getvalue().strip(), saved


def ask(
    df: pd.DataFrame,
    question: str,
    client: LLMClient,
    *,
    max_retries: int = 2,
    chart_path: str = "askcsv_chart.png",
) -> RunResult:
    """对一个 DataFrame 提一个问题，返回 RunResult。"""
    schema = describe_schema(df)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": build_user_message(schema, question)},
    ]

    last_err = ""
    code = ""
    for attempt in range(1, max_retries + 2):
        reply = client.chat(messages)
        code = extract_code(reply)
        try:
            answer, saved = _execute(code, df, chart_path)
            return RunResult(
                answer=answer or "（代码已执行，但没有 print 输出）",
                code=code,
                chart_path=saved,
                attempts=attempt,
                history=messages,
            )
        except Exception as exc:  # 把报错喂回给 LLM 让它自我修正
            last_err = f"{type(exc).__name__}: {exc}"
            messages.append({"role": "assistant", "content": reply})
            messages.append({"role": "user", "content": build_fix_message(code, last_err)})

    raise RuntimeError(f"尝试 {max_retries + 1} 次仍失败。最后的报错：{last_err}\n最后的代码：\n{code}")
