"""Vòng 2: A (tinh chỉnh TFT/TiDE), B (Chronos-2 có biến lịch), C (chấm lại cảnh báo), D (người dùng mới).

Cách dùng:  python src/extra.py A | B | C | D | summary
"""
import sys
import time

import numpy as np
import pandas as pd

from common import (ALERT_THRESHOLD, H_MAX, QCOLS, QUANTILES, RESULTS, SPLITS, conformal_quantiles, eval_frame,
                    load_daily, prob_over, save_preds, summarize)
from models import EXOG, calendar_exog, eval_rows, lgbm_rows, remaining_sum

HOLDOUT_FRAC = 0.2


def future_exog(uids, origin):
    return calendar_exog(pd.DataFrame({"unique_id": np.repeat(uids, H_MAX),
                                       "ds": np.tile(pd.date_range(origin + pd.Timedelta(days=1), periods=H_MAX), len(uids))}))


def fit_nf(name, mname, input_size, max_steps, train_users=None):
    from neuralforecast import NeuralForecast
    from neuralforecast.losses.pytorch import MSE
    from neuralforecast.models import TFT, TiDE

    daily = calendar_exog(load_daily(name))
    train = daily[daily["ds"] <= SPLITS[name]["train_end"]]
    if train_users is not None:
        train = train[train["unique_id"].isin(train_users)]
    kw = dict(h=H_MAX, input_size=input_size, loss=MSE(), max_steps=max_steps, scaler_type="robust", batch_size=64,
              windows_batch_size=256, random_seed=1, enable_progress_bar=False, logger=False, futr_exog_list=EXOG)
    model = TiDE(**kw) if mname == "TiDE" else TFT(**kw, hidden_size=64)
    nf = NeuralForecast(models=[model], freq="D")
    nf.fit(df=train)
    return nf


def nf_predict(nf, name, rows, hist_days=None):
    daily = calendar_exog(load_daily(name))
    preds = []
    for origin, r in rows.groupby("origin"):
        uids = r["unique_id"].unique()
        hist = daily[daily["unique_id"].isin(uids) & (daily["ds"] <= origin)]
        if hist_days:
            hist = hist[hist["ds"] > origin - pd.Timedelta(days=hist_days)]
        fc = nf.predict(df=hist, futr_df=future_exog(uids, origin)[["unique_id", "ds"] + EXOG])
        fc = fc.reset_index() if "unique_id" not in fc.columns else fc
        col = [c for c in fc.columns if c not in ("unique_id", "ds", "index")][0]
        preds.append(fc[["unique_id", "ds", col]].rename(columns={col: "value"}).assign(origin=origin))
    return rows.assign(pred=remaining_sum(rows, pd.concat(preds)))


# ---------------- A: tinh chỉnh TFT / TiDE ----------------

def run_A():
    rows_s = eval_rows("sparkov", load_daily("sparkov"))
    rows_p = eval_rows("personal_budget", load_daily("personal_budget"))
    for mname in ("TiDE", "TFT"):
        for input_size in (56, 112):
            tag = f"in{input_size}_s4000"
            t0 = time.time()
            nf = fit_nf("sparkov", mname, input_size, 4000)
            save_preds(conformal_quantiles(nf_predict(nf, "sparkov", rows_s)), "sparkov", f"{mname.lower()}_{tag}")
            save_preds(conformal_quantiles(nf_predict(nf, "personal_budget", rows_p)), "personal_budget",
                       f"{mname.lower()}_{tag}_from_sparkov")
            print(mname, tag, f"{time.time() - t0:.0f}s", flush=True)


# ---------------- B: Chronos-2 có biến lịch ----------------

def chronos_inputs(daily, rows, target_col, context_days):
    by = {u: g.reset_index(drop=True) for u, g in daily.groupby("unique_id")}
    inputs, base = [], np.empty(len(rows))
    for i, r in enumerate(rows.itertuples()):
        g = by[r.unique_id]
        k = (r.origin - g["ds"].iloc[0]).days
        ctx = g.iloc[max(0, k - context_days + 1) : k + 1]
        fut = future_exog([r.unique_id], r.origin)
        base[i] = ctx[target_col].iloc[-1]
        inputs.append({"target": ctx[target_col].to_numpy(np.float32),
                       "past_covariates": {e: ctx[e].to_numpy(np.float32) for e in EXOG},
                       "future_covariates": {e: fut[e].to_numpy(np.float32) for e in EXOG}})
    return inputs, base


def chronos_end_quantiles(pipe, daily, rows, context_days, cross=False):
    """Dự báo chuỗi cộng dồn; quantile tại bước N − d là quantile của tổng chi cuối tháng."""
    inputs, base = chronos_inputs(daily, rows, "rt", context_days)
    q, _ = pipe.predict_quantiles(inputs, prediction_length=H_MAX, quantile_levels=QUANTILES, cross_learning=cross)
    step = (rows["N"] - rows["d"]).to_numpy() - 1
    qend = np.sort(np.stack([np.asarray(q[i].float().cpu()).reshape(H_MAX, -1)[step[i]] for i in range(len(rows))]), axis=1)
    out = rows.copy()
    sdv = rows["S_d"].to_numpy()[:, None]
    out[QCOLS] = np.maximum(sdv + qend - base[:, None], sdv)
    out["pred"] = out["q0.5"]
    return out


def load_chronos():
    import torch
    from chronos import Chronos2Pipeline

    return Chronos2Pipeline.from_pretrained("amazon/chronos-2", device_map="cuda" if torch.cuda.is_available() else "cpu")


def run_B(context_days=365):
    pipe = load_chronos()
    for name in ("sparkov", "personal_budget"):
        daily = calendar_exog(load_daily(name))
        daily["rt"] = daily.groupby("unique_id")["y"].cumsum()
        rows = eval_rows(name, daily)
        save_preds(chronos_end_quantiles(pipe, daily, rows, context_days), name, "chronos2_rt_cov")
        save_preds(chronos_end_quantiles(pipe, daily, rows, context_days, cross=True), name, "chronos2_rt_cov_cross")
        # chuỗi chi theo ngày có biến lịch: tổng các giá trị trung bình là trung bình của tổng
        inputs, _ = chronos_inputs(daily, rows, "y", context_days)
        _, mean = pipe.predict_quantiles(inputs, prediction_length=H_MAX, quantile_levels=QUANTILES)
        pred = np.array([r.S_d + np.clip(np.asarray(mean[i].float().cpu()).ravel()[: r.N - r.d], 0, None).sum()
                         for i, r in enumerate(rows.itertuples())])
        save_preds(conformal_quantiles(rows.assign(pred=pred)), name, "chronos2_daily_cov")
        print("B done", name, flush=True)


# ---------------- C: chấm lại cảnh báo ----------------

def alert_metrics(q, budget, over, undecided):
    pov = prob_over(q, budget)
    a, o = (pov >= ALERT_THRESHOLD)[undecided], over[undecided]
    tp = np.sum(a & o)
    prec, rec = tp / max(a.sum(), 1), tp / max(o.sum(), 1)
    return {"precision": prec, "recall": rec, "F1": 2 * prec * rec / max(prec + rec, 1e-9),
            "brier": np.mean((pov[undecided] - o) ** 2)}


def run_C(name="sparkov", mults=(1.0, 1.1, 1.2)):
    ef = eval_frame(name)
    ef = ef[ef["split"] == "test"]
    out = []
    for mult in mults:
        B = ef["B"].to_numpy() * mult
        over, und = ef["S_N"].to_numpy() > B, ef["S_d"].to_numpy() <= B
        base = {"budget": f"x{mult}", "n_undecided": int(und.sum()), "overspend_rate": over[und].mean()}
        p = over[und].mean()
        out.append({**base, "model": "always_alert", "precision": p, "recall": 1.0, "F1": 2 * p / (1 + p), "brier": np.nan})
        for f in sorted(RESULTS.glob(f"preds_{name}_*.parquet")):
            pr = pd.read_parquet(f)
            fr = ef.merge(pr, on=["unique_id", "month", "d", "split"], how="left")
            if fr[QCOLS].isna().any().any():
                continue
            q = fr[QCOLS].to_numpy()
            row = {**base, "model": pr["model"].iloc[0], **alert_metrics(q, B, over, und)}
            for d in (5, 15, 25):
                m = (fr["d"] == d).to_numpy()
                row[f"F1_d{d}"] = alert_metrics(q[m], B[m], over[m], und[m])["F1"]
            out.append(row)
    res = pd.DataFrame(out)
    res.to_csv(RESULTS / f"round2_C_{name}.csv", index=False)
    with pd.option_context("display.float_format", "{:.3f}".format, "display.width", 250):
        print(res.sort_values(["budget", "F1"], ascending=[True, False]).to_string(index=False))


# ---------------- D: người dùng mới ----------------

def cold_lgbm(train_users, rows_test, k):
    """LightGBM chỉ dùng feature tính được từ k ngày gần nhất; thang đo lấy từ chính k ngày đó."""
    import lightgbm as lgb

    w = min(k, 28)

    def build(days):
        X, _, m = lgbm_rows("sparkov", days)
        s = m["scale"].to_numpy()
        sc = np.maximum(X[f"r{w}"].to_numpy() * s / 30.44, 1e-6)  # mức chi tháng ước từ k ngày gần nhất
        Xc = pd.DataFrame({"d": X["d"], "N": X["N"], "rem": X["rem"], "S_d": X["S_d"] * s / sc,
                           "runrate": X["runrate"] * s / sc, "r7": X["r7"] * s / sc, "act_frac": X["act_frac"],
                           "mx": X["mx"] * s / sc, "dow": X["dow"], "wknd_left": X["wknd_left"]})
        if k >= 14:
            Xc["r14"] = X["r14"] * s / sc
        return Xc, (m["S_N"] - m["S_d"]) / sc, m.assign(sc=sc)

    Xtr, ytr, mtr = build(range(1, 29))
    keep = ((mtr["split"] == "train") & mtr["unique_id"].isin(train_users)).to_numpy()
    Xev, _, mev = build([5, 10, 15, 20, 25])
    key = ["unique_id", "month", "d"]
    sel = mev.set_index(key).index.isin(rows_test.set_index(key).index)
    Xev, mev = Xev[sel].reset_index(drop=True), mev[sel].reset_index(drop=True)
    qp = np.empty((len(Xev), len(QUANTILES)))
    for j, q in enumerate(QUANTILES):
        mdl = lgb.LGBMRegressor(objective="quantile", alpha=q, n_estimators=500, learning_rate=0.05, num_leaves=31,
                                min_child_samples=50, subsample=0.8, subsample_freq=1, verbose=-1)
        qp[:, j] = mdl.fit(Xtr[keep], ytr[keep]).predict(Xev)
    out = mev.copy()
    out[QCOLS] = mev["S_d"].to_numpy()[:, None] + np.clip(np.sort(qp, axis=1), 0, None) * mev["sc"].to_numpy()[:, None]
    out["pred"] = out["q0.5"]
    return out


def run_D(ks=(14, 28)):
    daily = load_daily("sparkov")
    users = np.array(sorted(daily["unique_id"].unique()))
    hold = set(np.random.default_rng(42).choice(users, size=int(len(users) * HOLDOUT_FRAC), replace=False))
    train_users = [u for u in users if u not in hold]
    rows = eval_rows("sparkov", daily)
    test_hold = rows[rows["unique_id"].isin(hold) & (rows["split"] == "test")].reset_index(drop=True)
    val_seen = rows[~rows["unique_id"].isin(hold) & (rows["split"] == "val")].reset_index(drop=True)
    calib = pd.concat([val_seen, test_hold], ignore_index=True)  # conformal hiệu chỉnh trên val của user đã thấy
    dcal = calendar_exog(load_daily("sparkov"))
    dcal["rt"] = dcal.groupby("unique_id")["y"].cumsum()
    pipe = load_chronos()
    res = []
    for k in ks:
        preds = {"runrate": conformal_quantiles(calib.assign(pred=calib["S_d"] / calib["d"] * calib["N"]))}
        for mname in ("TiDE", "TFT"):
            nf = fit_nf("sparkov", mname, k, 2000, train_users=train_users)
            preds[mname.lower()] = conformal_quantiles(nf_predict(nf, "sparkov", calib, hist_days=k))
        preds["lgbm_cold"] = cold_lgbm(train_users, test_hold, k)
        preds["chronos2"] = chronos_end_quantiles(pipe, dcal, test_hold, k)
        for mname, fr in preds.items():
            test = fr[(fr["split"] == "test") & fr["unique_id"].isin(hold)]
            s = summarize(test)
            res.append({"history_days": k, "model": mname, "n": s["n"], "WAPE": s["WAPE"], "F1": s.get("F1"),
                        "cover80": s.get("cover80"), **{f"WAPE_d{d}": summarize(g)["WAPE"] for d, g in test.groupby("d")}})
            print(k, mname, round(s["WAPE"], 3), flush=True)
    pd.DataFrame(res).to_csv(RESULTS / "round2_D_sparkov.csv", index=False)


# ---------------- tổng hợp: WAPE trên val (để chọn cấu hình) và test ----------------

def summary():
    for name in ("sparkov", "personal_budget"):
        ef = eval_frame(name)
        rows = []
        for f in sorted(RESULTS.glob(f"preds_{name}_*.parquet")):
            p = pd.read_parquet(f)
            fr = ef.merge(p, on=["unique_id", "month", "d", "split"])
            r = {"model": p["model"].iloc[0]}
            for sp in ("val", "test"):
                g = fr[fr["split"] == sp]
                if len(g):
                    s = summarize(g)
                    r[f"{sp}_WAPE"], r[f"{sp}_cover80"] = s["WAPE"], s.get("cover80")
            rows.append(r)
        res = pd.DataFrame(rows).sort_values("test_WAPE")
        res.to_csv(RESULTS / f"round2_summary_{name}.csv", index=False)
        print("===", name)
        with pd.option_context("display.float_format", "{:.3f}".format, "display.width", 200):
            print(res.to_string(index=False))


if __name__ == "__main__":
    {"A": run_A, "B": run_B, "C": run_C, "D": run_D, "summary": summary}[sys.argv[1]]()
