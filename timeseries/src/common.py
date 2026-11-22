"""Khung đánh giá dùng chung: mốc dự báo, budget giả lập, conformal, chỉ số."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
RESULTS = ROOT / "results"

ORIGIN_DAYS = [5, 10, 15, 20, 25]
QUANTILES = [0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]
QCOLS = [f"q{q:g}" for q in QUANTILES]
ALERT_THRESHOLD = 0.30
H_MAX = 26  # số ngày còn lại tối đa: tháng 31 ngày, dự báo từ ngày 5

SPLITS = {
    "sparkov": {
        "val": ["2020-07", "2020-08", "2020-09"],
        "test": ["2020-10", "2020-11", "2020-12"],
        "train_end": "2020-06-30",
    },
    "personal_budget": {
        "val": [f"2023-{m:02d}" for m in range(9, 13)] + ["2024-01", "2024-02"],
        "test": [f"2024-{m:02d}" for m in range(3, 13)] + ["2025-01", "2025-02"],
        "train_end": "2023-08-31",
    },
    # TabFormer: dùng 2015-01 → 2020-01 (tháng 02/2020 thiếu ngày 29 nên bị loại khỏi bảng tháng)
    "tabformer": {
        "val": [f"2019-{m:02d}" for m in range(1, 7)],
        "test": [f"2019-{m:02d}" for m in range(7, 13)] + ["2020-01"],
        "train_end": "2018-12-31",
    },
}


def load_daily(name: str) -> pd.DataFrame:
    df = pd.read_parquet(PROCESSED / f"{name}_daily.parquet")
    df["ds"] = pd.to_datetime(df["ds"])
    return df.sort_values(["unique_id", "ds"]).reset_index(drop=True)


def monthly_table(daily: pd.DataFrame) -> pd.DataFrame:
    """Tổng chi mỗi tháng đủ ngày của từng user, kèm budget giả lập và thang đo từ 3 tháng trước."""
    d = daily.assign(month=daily["ds"].dt.to_period("M"))
    m = d.groupby(["unique_id", "month"]).agg(S_N=("y", "sum"), n_days=("y", "size")).reset_index()
    m["N"] = m["month"].dt.days_in_month
    m = m[m["n_days"] == m["N"]].copy()  # chỉ giữ tháng có đủ dữ liệu cả tháng
    m = m.sort_values(["unique_id", "month"])
    g = m.groupby("unique_id")
    prev = [g["S_N"].shift(k) for k in (1, 2, 3)]
    prev_month = [g["month"].shift(k) for k in (1, 2, 3)]
    contiguous = np.all([(prev_month[k - 1] == m["month"] - k).to_numpy() for k in (1, 2, 3)], axis=0)
    stacked = np.vstack([p.to_numpy() for p in prev])
    m["B"] = np.median(stacked, axis=0)        # budget giả lập: trung vị 3 tháng trước
    m["scale"] = np.mean(stacked, axis=0)      # thang đo của user: trung bình 3 tháng trước
    m["prev1"] = prev[0].to_numpy()
    m = m[contiguous].copy()
    m["month"] = m["month"].astype(str)
    return m.drop(columns="n_days").reset_index(drop=True)


def eval_frame(name: str, daily: pd.DataFrame | None = None, days=ORIGIN_DAYS) -> pd.DataFrame:
    """Mỗi dòng là một mốc dự báo (user, tháng, ngày d); cột split cho biết train, val hay test."""
    daily = load_daily(name) if daily is None else daily
    sp = SPLITS[name]
    m = monthly_table(daily)
    m["split"] = np.where(m["month"].isin(sp["val"]), "val", np.where(m["month"].isin(sp["test"]), "test", "train"))
    d = daily.assign(month=daily["ds"].dt.to_period("M").astype(str), dom=daily["ds"].dt.day)
    d["S"] = d.groupby(["unique_id", "month"])["y"].cumsum()
    rows = m.merge(pd.DataFrame({"d": list(days)}), how="cross")
    rows = rows.merge(d[["unique_id", "month", "dom", "S", "ds"]], left_on=["unique_id", "month", "d"], right_on=["unique_id", "month", "dom"])
    rows = rows.rename(columns={"S": "S_d", "ds": "origin"}).drop(columns="dom")
    return rows.reset_index(drop=True)


# ---------- phân phối và xác suất vượt budget ----------

def prob_over(qvals: np.ndarray, budget: np.ndarray, levels=QUANTILES) -> np.ndarray:
    """Nội suy CDF từ các quantile (mỗi dòng một dự báo) rồi lấy P(tổng > budget)."""
    lv = np.asarray(levels)
    q = np.sort(np.asarray(qvals, dtype=float), axis=1)  # chống quantile crossing
    out = np.empty(len(q))
    for i in range(len(q)):
        b = budget[i]
        if b <= q[i, 0]:
            out[i] = 1 - lv[0] / 2
        elif b >= q[i, -1]:
            out[i] = (1 - lv[-1]) / 2
        else:
            xs, idx = np.unique(q[i], return_index=True)
            out[i] = 1 - np.interp(b, xs, lv[idx])
    return out


def conformal_quantiles(frame: pd.DataFrame, pred_col="pred") -> pd.DataFrame:
    """Biến dự báo điểm thành quantile: tỷ lệ (thực tế − đã chi)/(dự báo − đã chi) trên tập val, theo từng d."""
    out = frame.copy()
    # Sàn 1% mức chi tháng: tránh chia gần 0 khi dự báo bằng đúng số đã chi
    rem_pred = np.maximum(out[pred_col] - out["S_d"], 0.01 * out["scale"])
    ratio = (out["S_N"] - out["S_d"]) / rem_pred
    for d, idx in out.groupby("d").groups.items():
        val_ratio = ratio.loc[idx][out.loc[idx, "split"] == "val"]
        qs = np.quantile(val_ratio, QUANTILES)
        for c, qv in zip(QCOLS, qs):
            out.loc[idx, c] = out.loc[idx, "S_d"] + rem_pred.loc[idx] * qv
    return out


# ---------- chỉ số ----------

def pinball(y, qvals, levels=QUANTILES):
    y = np.asarray(y)[:, None]
    lv = np.asarray(levels)[None, :]
    diff = y - qvals
    return np.mean(np.maximum(lv * diff, (lv - 1) * diff))


def summarize(frame: pd.DataFrame) -> dict:
    y, p = frame["S_N"].to_numpy(), frame["pred"].to_numpy()
    res = {"n": len(frame), "WAPE": np.abs(y - p).sum() / np.abs(y).sum()}
    over = y > frame["B"].to_numpy()
    res["base_rate"] = over.mean()
    if QCOLS[0] in frame and frame[QCOLS[0]].notna().all():
        q = frame[QCOLS].to_numpy()
        res["pinball_rel"] = pinball(y, q) / np.abs(y).mean()
        res["cover80"] = np.mean((y >= frame["q0.1"]) & (y <= frame["q0.9"]))
        pov = prob_over(q, frame["B"].to_numpy())
        alert = pov >= ALERT_THRESHOLD
        tp = np.sum(alert & over)
        res["precision"] = tp / max(alert.sum(), 1)
        res["recall"] = tp / max(over.sum(), 1)
        res["F1"] = 2 * res["precision"] * res["recall"] / max(res["precision"] + res["recall"], 1e-9)
        res["brier"] = np.mean((pov - over) ** 2)
    return res


def save_preds(frame: pd.DataFrame, dataset: str, model: str):
    RESULTS.mkdir(parents=True, exist_ok=True)
    keep = ["unique_id", "month", "d", "split", "pred"] + [c for c in QCOLS if c in frame]
    frame[keep].assign(model=model).to_parquet(RESULTS / f"preds_{dataset}_{model}.parquet", index=False)
