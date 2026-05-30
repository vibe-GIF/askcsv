"""生成一份示例销售数据，用来体验 askcsv。

    python examples/generate_sample.py   # 生成 sample_sales.csv
然后就可以：
    askcsv sample_sales.csv "哪个城市的销售额最高？"
    askcsv sample_sales.csv "线上和线下哪个渠道客单价更高？"
"""

import numpy as np
import pandas as pd

rng = np.random.default_rng(7)
N = 800

city = rng.choice(["北京", "上海", "广州", "深圳", "成都"], N, p=[.3, .25, .2, .15, .1])
channel = rng.choice(["线上", "线下"], N, p=[.6, .4])
category = rng.choice(["数码", "服饰", "食品", "家居"], N)
qty = rng.integers(1, 6, N)
price = rng.normal(200, 80, N).clip(20, None).round(2)

df = pd.DataFrame({
    "order_id": range(1, N + 1),
    "city": city,
    "channel": channel,
    "category": category,
    "quantity": qty,
    "price": price,
    "amount": (qty * price).round(2),
    "date": pd.to_datetime("2024-01-01") + pd.to_timedelta(rng.integers(0, 365, N), "D"),
})

df.to_csv("sample_sales.csv", index=False, encoding="utf-8-sig")
print(f"✓ 已生成 sample_sales.csv（{len(df)} 行）。试试：")
print('  askcsv sample_sales.csv "哪个城市的销售额最高？"')
