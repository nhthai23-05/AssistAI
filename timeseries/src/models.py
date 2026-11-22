"""Chạy các mô hình dự báo chi tiêu cuối tháng và đánh giá.

Cách dùng:  python src/models.py <lệnh> <dataset> [tham số]
  lệnh: baselines | ets | lgbm [train_dataset] | nf [tên mô hình...] | chronos | evaluate
"""
import calendar
import sys
import time

import numpy as np
import pandas as pd

from common import (H_MAX, QCOLS, QUANTILES, RESULTS, SPLITS, conformal_quantiles, eval_frame,
                    load_daily, monthly_table, save_preds, summarize)


def series_dict(daily, col="y"):
    return {uid: (g["ds"].iloc[0], g[col].to_numpy()) for uid, g in daily.groupby("unique_id")}


def eval_rows(name, daily):
    ef = eval_frame(name, daily)
    return ef[ef["split"] != "train"].reset_index(drop=True)


def remaining_sum(rows, daily_pred):
    """daily_pred: unique_id, origin, ds, value (dự báo theo ngày) → đã chi + tổng các ngày còn lại của tháng."""
    piv = {k: g["value"].to_numpy() for k, g in daily_pred.sort_values("ds").groupby(["unique_id", "origin"])}
    return np.array([r.S_d + np.clip(piv[(r.unique_id, r.origin)][: r.N - r.d], 0, None).sum() for r in rows.itertuples()])


# ---------------- baseline ----------------

def run_baselines(name):
    daily = load_daily(name)
    ef = eval_rows(name, daily)
    sd = series_dict(daily)
    rng = np.random.default_rng(0)
    snaive, boot = np.empty(len(ef)), np.empty((len(ef), len(QUANTILES)))
    for i, r in enumerate(ef.itertuples()):
        start, v = sd[r.unique_id]
        k = (r.origin - start).days
        rem = r.N - r.d
        last7 = v[k - 6 : k + 1]
        snaive[i] = r.S_d + last7.sum() * (rem // 7) + last7[: rem % 7].sum()
        pool = v[max(0, k - 90) : k + 1]
        boot[i] = np.quantile(r.S_d + rng.choice(pool, size=(1000, rem)).sum(axis=1), QUANTILES)
    point = {
        "runrate": ef["S_d"] / ef["d"] * ef["N"],
        "hist_mean": ef["S_d"] + (ef["N"] - ef["d"]) * ef["scale"] / 30.44,
        "last_month": np.maximum(ef["S_d"], ef["prev1"]),
        "snaive7": snaive,
    }
    for model, pred in point.items():
        save_preds(conformal_quantiles(ef.assign(pred=pred)), name, model)
    b = ef.assign(pred=boot[:, QUANTILES.index(0.5)])
    b[QCOLS] = boot
    save_preds(b, name, "bootstrap")


# ---------------- ETS ----------------

def run_ets(name):
    from statsforecast import StatsForecast
    from statsforecast.models import AutoETS

    daily = load_daily(name)
    ef = eval_rows(name, daily)
    preds = []
    for origin, rows in ef.groupby("origin"):
        hist = daily[daily["unique_id"].isin(rows["unique_id"]) & (daily["ds"] <= origin) & (daily["ds"] > origin - pd.Timedelta(days=365))]
        fc = StatsForecast(models=[AutoETS(season_length=7)], freq="D", n_jobs=-1).forecast(df=hist, h=H_MAX)
        preds.append(fc.reset_index().rename(columns={"AutoETS": "value"}).assign(origin=origin)[["unique_id", "origin", "ds", "value"]])
    save_preds(conformal_quantiles(ef.assign(pred=remaining_sum(ef, pd.concat(preds)))), name, "ets")


# ---------------- LightGBM: dự báo thẳng phần chi còn lại ----------------

def weekend_left(month_str, d):
    y, m = map(int, month_str.split("-"))
    return sum(calendar.weekday(y, m, t) >= 5 for t in range(d + 1, calendar.monthrange(y, m)[1] + 1))


def lgbm_rows(name, days):
    """Feature tại ngày d, chuẩn hóa theo thang đo của user (trung bình 3 tháng trước)."""
    daily = load_daily(name)
    m = monthly_table(daily)
    sp = SPLITS[name]
    m["split"] = np.where(m["month"].isin(sp["val"]), "val", np.where(m["month"].isin(sp["test"]), "test", "train"))
    d = daily.assign(month=daily["ds"].dt.to_period("M").astype(str), dom=daily["ds"].dt.day)
    gm = d.groupby(["unique_id", "month"])
    d["S"] = gm["y"].cumsum()
    d["act"] = (d["y"] > 0).astype(int).groupby([d["unique_id"], d["month"]]).cumsum()
    d["mx"] = gm["y"].cummax()
    for w in (7, 14, 28):
        d[f"r{w}"] = d.groupby("unique_id")["y"].transform(lambda s, w=w: s.rolling(w, min_periods=1).sum())
    prev = d[["unique_id", "month", "dom", "S"]].copy()
    prev["month"] = (pd.PeriodIndex(prev["month"], freq="M") + 1).astype(str)
    d = d.merge(prev.rename(columns={"S": "S_prev"}), on=["unique_id", "month", "dom"], how="left")
    rows = d[d["dom"].isin(list(days))].merge(m, on=["unique_id", "month"])
    s = rows["scale"]
    X = pd.DataFrame({
        "d": rows["dom"], "N": rows["N"], "rem": rows["N"] - rows["dom"],
        "S_d": rows["S"] / s, "runrate": rows["S"] / rows["dom"] * rows["N"] / s,
        "r7": rows["r7"] / s * 30.44 / 7, "r14": rows["r14"] / s * 30.44 / 14, "r28": rows["r28"] / s * 30.44 / 28,
        "prev1": rows["prev1"] / s, "S_prev": rows["S_prev"] / s, "B": rows["B"] / s,
        "act_frac": rows["act"] / rows["dom"], "mx": rows["mx"] / s, "dow": rows["ds"].dt.dayofweek,
    })
    X["wknd_left"] = [weekend_left(mo, dd) for mo, dd in zip(rows["month"], rows["dom"])]
    target = (rows["S_N"] - rows["S"]) / s
    meta = rows[["unique_id", "month", "split", "S_N", "N", "B", "scale"]].assign(d=rows["dom"], S_d=rows["S"])
    return X, target, meta


def run_lgbm(name, train_name=None):
    import lightgbm as lgb

    train_name = train_name or name
    Xtr, ytr, mtr = lgbm_rows(train_name, range(1, 29))
    keep = (mtr["split"] == "train").to_numpy()
    Xev, _, mev = lgbm_rows(name, [5, 10, 15, 20, 25])
    ev = (mev["split"] != "train").to_numpy()
    Xev, mev = Xev[ev].reset_index(drop=True), mev[ev].reset_index(drop=True)
    qpred = np.empty((len(Xev), len(QUANTILES)))
    for j, q in enumerate(QUANTILES):
        mdl = lgb.LGBMRegressor(objective="quantile", alpha=q, n_estimators=500, learning_rate=0.05, num_leaves=31,
                                min_child_samples=50, subsample=0.8, subsample_freq=1, verbose=-1)
        mdl.fit(Xtr[keep], ytr[keep])
        qpred[:, j] = mdl.predict(Xev)
    out = mev.copy()
    out[QCOLS] = mev["S_d"].to_numpy()[:, None] + np.clip(np.sort(qpred, axis=1), 0, None) * mev["scale"].to_numpy()[:, None]
    out["pred"] = out["q0.5"]
    save_preds(out, name, "lgbm" if train_name == name else f"lgbm_from_{train_name}")


# ---------------- neuralforecast: DLinear, TiDE, TFT ----------------

EXOG = ["dom", "dow", "wknd", "left"]


def calendar_exog(df):
    return df.assign(dom=df["ds"].dt.day / 31.0, dow=df["ds"].dt.dayofweek / 6.0,
                     wknd=(df["ds"].dt.dayofweek >= 5).astype(float),
                     left=(df["ds"].dt.days_in_month - df["ds"].dt.day) / 31.0)


def run_nf(name, models=("DLinear", "TiDE", "TFT"), max_steps=1500):
    from neuralforecast import NeuralForecast
    from neuralforecast.losses.pytorch import MSE
    from neuralforecast.models import TFT, DLinear, TiDE

    daily = calendar_exog(load_daily(name))
    train = daily[daily["ds"] <= SPLITS[name]["train_end"]]
    kw = dict(h=H_MAX, input_size=56, loss=MSE(), max_steps=max_steps, scaler_type="robust", batch_size=64,
              windows_batch_size=256, random_seed=1, enable_progress_bar=False, logger=False)
    builders = {
        "DLinear": lambda: DLinear(**kw),
        "TiDE": lambda: TiDE(**kw, futr_exog_list=EXOG),
        "TFT": lambda: TFT(**kw, futr_exog_list=EXOG, hidden_size=64),
    }
    ef = eval_rows(name, daily)
    for mname in models:
        t0 = time.time()
        nf = NeuralForecast(models=[builders[mname]()], freq="D")
        nf.fit(df=train)
        preds = []
        for origin, rows in ef.groupby("origin"):
            uids = rows["unique_id"].unique()
            hist = daily[daily["unique_id"].isin(uids) & (daily["ds"] <= origin)]
            fut = calendar_exog(pd.DataFrame({"unique_id": np.repeat(uids, H_MAX),
                                              "ds": np.tile(pd.date_range(origin + pd.Timedelta(days=1), periods=H_MAX), len(uids))}))
            fc = nf.predict(df=hist, futr_df=fut[["unique_id", "ds"] + EXOG])
            fc = fc.reset_index() if "unique_id" not in fc.columns else fc
            col = [c for c in fc.columns if c not in ("unique_id", "ds", "index")][0]
            preds.append(fc[["unique_id", "ds", col]].rename(columns={col: "value"}).assign(origin=origin))
        save_preds(conformal_quantiles(ef.assign(pred=remaining_sum(ef, pd.concat(preds)))), name, mname.lower())
        print(mname, f"{time.time() - t0:.0f}s", flush=True)


# ---------------- Chronos-2 zero-shot ----------------

def run_chronos(name, context_days=365, model_id="amazon/chronos-2"):
    """Dự báo chuỗi chi cộng dồn: quantile tại bước N − d chính là quantile của tổng chi cuối tháng."""
    import torch
    from chronos import Chronos2Pipeline

    pipe = Chronos2Pipeline.from_pretrained(model_id, device_map="cuda" if torch.cuda.is_available() else "cpu")
    daily = load_daily(name)
    daily["rt"] = daily.groupby("unique_id")["y"].cumsum()
    ef = eval_rows(name, daily)
    sd = series_dict(daily, "rt")
    contexts, base = [], np.empty(len(ef))
    for i, r in enumerate(ef.itertuples()):
        start, rt = sd[r.unique_id]
        k = (r.origin - start).days
        ctx = rt[max(0, k - context_days + 1) : k + 1]
        base[i] = ctx[-1]
        contexts.append(torch.tensor(ctx, dtype=torch.float32))
    qs = []
    for b in range(0, len(contexts), 256):
        q, _ = pipe.predict_quantiles(contexts[b : b + 256], prediction_length=H_MAX, quantile_levels=QUANTILES)
        qs.extend(np.asarray(x.float().cpu()).reshape(H_MAX, len(QUANTILES)) for x in q)
    step = (ef["N"] - ef["d"]).to_numpy() - 1
    qend = np.sort(np.stack([qs[i][step[i]] for i in range(len(ef))]), axis=1)
    out = ef.copy()
    sdv = ef["S_d"].to_numpy()[:, None]
    out[QCOLS] = np.maximum(sdv + qend - base[:, None], sdv)
    out["pred"] = out["q0.5"]
    save_preds(out, name, "chronos2")


# ---------------- đánh giá ----------------

def evaluate(name):
    ef = eval_frame(name)
    rows = []
    for f in sorted(RESULTS.glob(f"preds_{name}_*.parquet")):
        p = pd.read_parquet(f)
        test = ef.merge(p, on=["unique_id", "month", "d", "split"])
        test = test[test["split"] == "test"]
        row = {"model": p["model"].iloc[0], **summarize(test)}
        for d, g in test.groupby("d"):
            row[f"WAPE_d{d}"] = summarize(g)["WAPE"]
        rows.append(row)
    res = pd.DataFrame(rows).sort_values("WAPE")
    res.to_csv(RESULTS / f"summary_{name}.csv", index=False)
    with pd.option_context("display.float_format", "{:.3f}".format, "display.width", 250, "display.max_columns", 30):
        print(res.to_string(index=False))


if __name__ == "__main__":
    cmd, name, extra = sys.argv[1], sys.argv[2], sys.argv[3:]
    if cmd == "baselines":
        run_baselines(name)
    elif cmd == "ets":
        run_ets(name)
    elif cmd == "lgbm":
        run_lgbm(name, *extra[:1])
    elif cmd == "nf":
        run_nf(name, models=tuple(extra) or ("DLinear", "TiDE", "TFT"))
    elif cmd == "chronos":
        run_chronos(name)
    elif cmd == "evaluate":
        evaluate(name)
