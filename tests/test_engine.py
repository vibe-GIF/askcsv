"""不依赖真实 API 的单元测试：用假的 LLM client 返回固定代码。"""

import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from askcsv import engine  # noqa: E402
from askcsv.engine import ask, describe_schema, extract_code  # noqa: E402


class FakeClient:
    """按预设脚本依次返回回复，模拟多轮（含纠错）对话。"""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def chat(self, messages, temperature=0.0):
        self.calls += 1
        return self.replies.pop(0)


@pytest.fixture
def df():
    return pd.DataFrame(
        {"city": ["北京", "上海", "北京"], "sales": [10, 20, 30]}
    )


def test_extract_code_from_fence():
    text = "随便说点\n```python\nprint(1+1)\n```\n结尾"
    assert extract_code(text) == "print(1+1)"


def test_describe_schema_mentions_columns(df):
    s = describe_schema(df)
    assert "city" in s and "sales" in s and "3 行" in s


def test_ask_runs_generated_code(df):
    code = '```python\ntotal = df.groupby("city")["sales"].sum().max()\nprint(f"最高 {total}")\n```'
    res = ask(df, "哪个城市销售额最高？", FakeClient([code]))
    assert "最高 40" in res.answer
    assert res.attempts == 1


def test_ask_retries_on_error(df):
    bad = "```python\nprint(undefined_var)\n```"
    good = '```python\nprint("ok", df["sales"].sum())\n```'
    client = FakeClient([bad, good])
    res = ask(df, "求和", client, max_retries=2)
    assert "ok 60" in res.answer
    assert res.attempts == 2  # 第一次失败，第二次成功


def test_forbidden_code_is_blocked(df):
    evil = "```python\nimport os\nos.system('echo hacked')\n```"
    # 连续返回危险代码，应当在重试用尽后抛错而不是执行
    client = FakeClient([evil, evil, evil])
    with pytest.raises(RuntimeError):
        ask(df, "删库", client, max_retries=2)


def test_chart_is_saved(tmp_path, df):
    code = '```python\ndf.groupby("city")["sales"].sum().plot(kind="bar")\nprint("done")\n```'
    out = str(tmp_path / "c.png")
    res = ask(df, "画图", FakeClient([code]), chart_path=out)
    assert res.chart_path == out
    assert os.path.exists(out)
