"""askcsv —— 用大白话问数据，AI 帮你跑分析。

    >>> import askcsv
    >>> df = askcsv.load_data("data.csv")
    >>> res = askcsv.ask(df, "哪个城市的销售额最高？", askcsv.LLMClient())
    >>> print(res.answer)

命令行：
    $ askcsv data.csv "哪个城市的销售额最高？"
    $ askcsv data.csv          # 进入交互问答模式
"""

from __future__ import annotations

from .engine import RunResult, ask, describe_schema, load_data
from .llm import LLMClient, LLMError

__version__ = "0.1.0"
__all__ = [
    "ask",
    "load_data",
    "describe_schema",
    "RunResult",
    "LLMClient",
    "LLMError",
    "__version__",
]
