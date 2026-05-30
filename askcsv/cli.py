"""命令行入口：
    askcsv data.csv "问题"     一次问答
    askcsv data.csv            进入交互模式，连续提问
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .engine import ask, load_data
from .llm import LLMClient, LLMError


def _force_utf8() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # type: ignore[union-attr]
        except Exception:
            pass


def _print_result(res, show_code: bool) -> None:
    print("\n💡 " + res.answer.replace("\n", "\n   "))
    if res.chart_path:
        print(f"\n📊 图已保存：{res.chart_path}")
    if show_code:
        print(f"\n🧩 生成的代码（尝试 {res.attempts} 次）：\n{res.code}")


def main(argv: list[str] | None = None) -> int:
    _force_utf8()
    parser = argparse.ArgumentParser(
        prog="askcsv",
        description="用大白话问数据，AI 帮你写 pandas、跑分析、画图。",
    )
    parser.add_argument("data", help="数据文件（csv/tsv/xlsx/parquet/json）")
    parser.add_argument("question", nargs="?", help="要问的问题；省略则进入交互模式")
    parser.add_argument("--model", help="模型名（覆盖 ASKCSV_MODEL）")
    parser.add_argument("--show-code", action="store_true", help="同时打印 AI 生成的代码")
    parser.add_argument("--encoding", help="读取文件的编码，如 gbk")
    parser.add_argument("--sep", help="分隔符，如 ';'")
    parser.add_argument("-v", "--version", action="version", version=f"askcsv {__version__}")
    args = parser.parse_args(argv)

    read_kwargs = {}
    if args.encoding:
        read_kwargs["encoding"] = args.encoding
    if args.sep:
        read_kwargs["sep"] = args.sep

    try:
        df = load_data(args.data, **read_kwargs)
    except FileNotFoundError:
        print(f"✗ 找不到文件：{args.data}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"✗ 读取失败：{exc}", file=sys.stderr)
        return 1

    print(f"✓ 已加载 {args.data}：{len(df)} 行 × {df.shape[1]} 列")

    try:
        client = LLMClient(model=args.model)
    except LLMError as exc:
        print(f"✗ {exc}", file=sys.stderr)
        return 1

    # 一次性提问
    if args.question:
        return _ask_once(df, args.question, client, args.show_code)

    # 交互模式
    print("进入交互问答模式，输入问题后回车；输入 q 或 exit 退出。\n")
    while True:
        try:
            q = input("❓ ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见 👋")
            return 0
        if q.lower() in ("q", "quit", "exit", ""):
            print("再见 👋")
            return 0
        _ask_once(df, q, client, args.show_code)
        print()


def _ask_once(df, question: str, client: LLMClient, show_code: bool) -> int:
    try:
        res = ask(df, question, client)
    except LLMError as exc:
        print(f"✗ 模型调用失败：{exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001
        print(f"✗ 分析失败：{exc}", file=sys.stderr)
        return 1
    _print_result(res, show_code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
