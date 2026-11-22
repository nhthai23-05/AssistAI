"""Đưa dữ liệu giao dịch về chuỗi chi tiêu theo ngày: (unique_id, ds, y).

Ngày không có giao dịch được điền 0, trong khoảng từ ngày đầu đến ngày cuối của mỗi người dùng.
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "data" / "processed"


def tabformer_to_parquet():
    """CSV 2,2 GB của TabFormer → parquet gọn (chỉ các cột cần), chạy một lần."""
    import pyarrow.csv as pv

    cols = ["User", "Card", "Year", "Month", "Day", "Amount", "Use Chip", "Merchant Name", "MCC", "Is Fraud?"]
    t = pv.read_csv(RAW / "tabformer" / "credit_card_transactions-ibm_v2.csv",
                    convert_options=pv.ConvertOptions(include_columns=cols))
    df = t.to_pandas()
    df["Amount"] = df["Amount"].str.replace("$", "", regex=False).astype(float)
    INTERIM.mkdir(parents=True, exist_ok=True)
    df.to_parquet(INTERIM / "tabformer_tx.parquet", index=False)
    return df


def to_daily(tx: pd.DataFrame) -> pd.DataFrame:
    """tx: unique_id, ds (datetime), amount → panel đủ ngày, ngày không chi = 0."""
    tx = tx.assign(ds=tx["ds"].dt.normalize())
    daily = tx.groupby(["unique_id", "ds"], as_index=False)["amount"].sum().rename(columns={"amount": "y"})
    parts = []
    for uid, g in daily.groupby("unique_id"):
        idx = pd.date_range(g["ds"].min(), g["ds"].max(), freq="D")
        parts.append(g.set_index("ds")["y"].reindex(idx, fill_value=0.0).rename_axis("ds").reset_index().assign(unique_id=uid))
    return pd.concat(parts, ignore_index=True)[["unique_id", "ds", "y"]]


def prepare_sparkov() -> pd.DataFrame:
    cols = ["trans_date_trans_time", "cc_num", "amt", "is_fraud"]
    tx = pd.concat([pd.read_csv(RAW / "sparkov" / f, usecols=cols) for f in ["fraudTrain.csv", "fraudTest.csv"]], ignore_index=True)
    tx = tx[tx["is_fraud"] == 0]  # giao dịch gian lận không phải hành vi chi tiêu của người dùng
    tx = pd.DataFrame({"unique_id": tx["cc_num"].astype(str), "ds": pd.to_datetime(tx["trans_date_trans_time"]), "amount": tx["amt"]})
    return to_daily(tx)


def prepare_personal_budget() -> pd.DataFrame:
    p = pd.read_csv(RAW / "personal_budget" / "11 march 2025.csv")
    ds = pd.to_datetime(p["date"], utc=True).dt.tz_localize(None)
    tx = pd.DataFrame({"unique_id": "pb", "ds": ds, "amount": p["amount"].clip(lower=0)})
    return to_daily(tx)


TABFORMER_START = "2015-01-01"  # 5 năm gần nhất; dữ liệu kết thúc 28/02/2020


def prepare_tabformer() -> pd.DataFrame:
    tx = load_transactions("tabformer")
    tx = tx[(tx["amount"] > 0) & ~tx["fraud"]]  # bỏ hoàn tiền (số âm) và gian lận
    return to_daily(tx[["unique_id", "ds", "amount"]])


def load_transactions(name: str) -> pd.DataFrame:
    """Giao dịch thô dạng chung: unique_id, ds, amount (giữ cả số âm), category_raw, category (AssistAI), fraud."""
    from categories import PERSONAL_BUDGET, SPARKOV, mcc_to_assistai

    if name == "sparkov":
        cols = ["trans_date_trans_time", "cc_num", "category", "amt", "is_fraud"]
        t = pd.concat([pd.read_csv(RAW / "sparkov" / f, usecols=cols) for f in ["fraudTrain.csv", "fraudTest.csv"]],
                      ignore_index=True)
        out = pd.DataFrame({"unique_id": t["cc_num"].astype(str), "ds": pd.to_datetime(t["trans_date_trans_time"]),
                            "amount": t["amt"], "category_raw": t["category"], "fraud": t["is_fraud"] == 1})
        out["category"] = out["category_raw"].map(SPARKOV)
    elif name == "personal_budget":
        p = pd.read_csv(RAW / "personal_budget" / "11 march 2025.csv")
        out = pd.DataFrame({"unique_id": "pb", "ds": pd.to_datetime(p["date"], utc=True).dt.tz_localize(None),
                            "amount": p["amount"], "category_raw": p["category"], "fraud": False})
        out["category"] = out["category_raw"].map(PERSONAL_BUDGET)
    elif name == "tabformer":
        t = pd.read_parquet(INTERIM / "tabformer_tx.parquet")
        ds = pd.to_datetime(dict(year=t["Year"], month=t["Month"], day=t["Day"]))
        keep = ds >= TABFORMER_START
        t, ds = t[keep], ds[keep]
        out = pd.DataFrame({"unique_id": "u" + t["User"].astype(str), "ds": ds, "amount": t["Amount"],
                            "category_raw": t["MCC"], "fraud": t["Is Fraud?"] == "Yes", "channel": t["Use Chip"]})
        codes = out["category_raw"].unique()
        out["category"] = out["category_raw"].map({c: mcc_to_assistai(int(c)) for c in codes})
    else:
        raise ValueError(name)
    return out.sort_values(["unique_id", "ds"]).reset_index(drop=True)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = {"sparkov": prepare_sparkov, "personal_budget": prepare_personal_budget, "tabformer": prepare_tabformer}
    import sys
    for name, fn in [(n, jobs[n]) for n in (sys.argv[1:] or jobs)]:
        df = fn()
        df.to_parquet(OUT / f"{name}_daily.parquet", index=False)
        print(name, df.shape, df["unique_id"].nunique(), "series", df["ds"].min().date(), "→", df["ds"].max().date())
