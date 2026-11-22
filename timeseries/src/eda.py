"""EDA cho các bộ dữ liệu chi tiêu.

Cách dùng:  python src/eda.py <dataset> [số user lấy mẫu, mặc định 300]
Kết quả:    eda/<dataset>/*.png (hình) và eda/<dataset>/stats.json (toàn bộ con số dùng trong BAO_CAO_EDA.md)

Các phần:
  1. profile      - quy mô, phân phối số tiền, độ thưa (ADI/CV²), cơ cấu danh mục AssistAI
  2. calendar     - mùa vụ theo thứ, ngày trong tháng, tháng trong năm; đường chi tích lũy trong tháng
  3. stationarity - ADF + KPSS trên chuỗi ngày, tuần, tháng
  4. dependence   - ACF/PACF, Ljung-Box, STL (độ mạnh mùa vụ/xu hướng), bậc AR, phụ thuộc giữa các tháng
  5. categories   - tương quan giữa danh mục, Granger, đóng góp phương sai vào tổng tháng
  6. features     - tương quan feature–mục tiêu, so sánh độ dài cửa sổ trượt / MA / EWMA
"""
import contextlib
import io
import json
import sys
import warnings

import matplotlib
import matplotlib.ticker

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.patches import Patch
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.ar_model import ar_select_order
from statsmodels.tsa.seasonal import STL
from statsmodels.tsa.stattools import acf, adfuller, grangercausalitytests, kpss, pacf

from common import ROOT, eval_frame, load_daily, monthly_table
from prepare import load_transactions

warnings.simplefilter("ignore")

# Bảng màu (dataviz reference palette, light): danh mục theo thứ tự cố định
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
INK, MUTED, GRID, SURF = "#1f1f1e", "#6b6b68", "#e6e5e1", "#fcfcfb"
DIVERGING = LinearSegmentedColormap.from_list("div", ["#e34948", "#f0efec", "#1c5cab"])
plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "axes.edgecolor": GRID, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "font.size": 10, "axes.titlesize": 11,
    "axes.titleweight": "bold", "legend.frameon": False, "lines.linewidth": 2,
})
DOW = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]


def save(fig, out, name):
    fig.tight_layout()
    fig.savefig(out / f"{name}.png", dpi=110, bbox_inches="tight")
    plt.close(fig)


def desc(x) -> dict:
    x = pd.Series(np.asarray(x, dtype=float)).dropna()
    if len(x) == 0:
        return {}
    return {"n": int(len(x)), "mean": x.mean(), "p10": x.quantile(0.1), "median": x.median(), "p90": x.quantile(0.9)}


def sbc_class(adi, cv2):
    """Syntetos–Boylan–Croston (2005): ngưỡng ADI 1.32, CV² 0.49."""
    if adi < 1.32:
        return "smooth" if cv2 < 0.49 else "erratic"
    return "intermittent" if cv2 < 0.49 else "lumpy"


def adi_cv2(y):
    nz = y[y > 0]
    if len(nz) < 2:
        return np.nan, np.nan
    return len(y) / len(nz), (nz.std() / nz.mean()) ** 2


def cat_daily(tx, ids):
    """uid → DataFrame ngày × danh mục (đủ ngày, ngày không chi = 0)."""
    t = tx[tx["unique_id"].isin(ids)]
    t = t.assign(day=t["ds"].dt.normalize())
    out = {}
    for uid, g in t.groupby("unique_id"):
        p = g.pivot_table(index="day", columns="category", values="amount", aggfunc="sum", fill_value=0.0)
        out[uid] = p.reindex(pd.date_range(p.index.min(), p.index.max(), freq="D"), fill_value=0.0)
    return out


# ---------------------------------------------------------------- 1. profile

def profile(tx_all, daily, catd, out):
    res = {"n_tx": len(tx_all), "n_users": int(tx_all["unique_id"].nunique()),
           "start": str(tx_all["ds"].min().date()), "end": str(tx_all["ds"].max().date()),
           "refund_share": float((tx_all["amount"] <= 0).mean()), "fraud_share": float(tx_all["fraud"].mean())}
    tx = tx_all[(tx_all["amount"] > 0) & ~tx_all["fraud"]]
    a = tx["amount"]
    res["amount"] = {**desc(a), "p99": a.quantile(0.99), "max": a.max(), "skew": stats.skew(a),
                     "skew_log": stats.skew(np.log(a))}
    per_day = tx.groupby(["unique_id", tx["ds"].dt.normalize()]).size()
    res["tx_per_active_day"] = desc(per_day)
    res["days_per_user"] = desc(daily.groupby("unique_id").size())

    g = daily.groupby("unique_id")["y"]
    res["zero_day_share"] = desc(g.apply(lambda s: (s == 0).mean()))
    res["daily_spend"] = desc(g.mean())

    # Độ thưa của chuỗi tổng và chuỗi từng danh mục (SBC)
    tot = pd.DataFrame([adi_cv2(s.to_numpy()) for _, s in g], columns=["adi", "cv2"]).dropna()
    tot["cls"] = [sbc_class(x, y) for x, y in zip(tot["adi"], tot["cv2"])]
    cat_rows = []
    for uid, p in catd.items():
        for c in p.columns:
            adi, cv2 = adi_cv2(p[c].to_numpy())
            if not np.isnan(adi):
                cat_rows.append((uid, c, adi, cv2, sbc_class(adi, cv2)))
    cat = pd.DataFrame(cat_rows, columns=["uid", "category", "adi", "cv2", "cls"])
    res["sbc_total"] = tot["cls"].value_counts(normalize=True).to_dict()
    res["sbc_category"] = cat["cls"].value_counts(normalize=True).to_dict()
    res["sbc_category_by_cat"] = cat.groupby("category")["cls"].agg(lambda s: s.value_counts(normalize=True).to_dict()).to_dict()
    res["adi_category_median"] = cat.groupby("category")["adi"].median().to_dict()

    # Mức tập trung: phần chi từ 5% giao dịch lớn nhất của mỗi user
    def top_share(v):
        v = np.sort(v)[::-1]
        k = max(1, int(np.ceil(0.05 * len(v))))
        return v[:k].sum() / v.sum()
    res["top5pct_tx_spend_share"] = desc(tx.groupby("unique_id")["amount"].apply(lambda s: top_share(s.to_numpy())))
    # Tháng có một giao dịch ≥ 50% chi cả tháng (kiểu "trả nợ", "tiền nhà")
    tm = tx.assign(month=tx["ds"].dt.to_period("M"))
    mt = tm.groupby(["unique_id", "month"])["amount"].agg(["sum", "max"])
    res["month_with_single_tx_ge50pct"] = float((mt["max"] >= 0.5 * mt["sum"]).mean())

    share = tx.groupby("category")["amount"].sum().sort_values(ascending=False)
    res["category_spend_share"] = (share / share.sum()).to_dict()
    res["category_count_share"] = tx["category"].value_counts(normalize=True).to_dict()

    fig, ax = plt.subplots(figsize=(6.4, 3.4))
    ax.hist(np.log10(a), bins=80, color=C[0], edgecolor=SURF, linewidth=0.3)
    ax.set_xlabel("log10(số tiền một giao dịch)")
    ax.set_ylabel("số giao dịch")
    ax.set_title("Phân phối số tiền giao dịch (thang log)")
    save(fig, out, "1a_amount_hist")

    fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.8), sharey=True)
    for ax, d, ttl in [(axes[0], tot, "Chuỗi tổng chi/ngày của mỗi user"), (axes[1], cat, "Chuỗi từng danh mục × user")]:
        ax.scatter(d["adi"], d["cv2"], s=12, alpha=0.35 if len(d) > 50 else 0.9, color=C[0], linewidths=0)
        ax.axvline(1.32, color=MUTED, lw=1, ls="--")
        ax.axhline(0.49, color=MUTED, lw=1, ls="--")
        ax.set_xscale("log")
        ax.set_yscale("log")
        for axis in (ax.xaxis, ax.yaxis):
            axis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:g}"))
            axis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        hi = max(2.0, float(d["adi"].max()) * 1.15)
        ax.set_xlim(0.95, hi)
        ticks = (1, 1.32, 2, 5) if hi < 10 else (1, 2, 5, 10, 20, 50, 100)
        ax.set_xticks([t for t in ticks if t <= hi])
        ax.set_xlabel("ADI (khoảng cách TB giữa 2 ngày có chi, log)")
        ax.set_title(ttl)
    axes[0].set_ylabel("CV² (biến động khi có chi, log)")
    fig.text(0.5, -0.02, "Vạch đứt: ngưỡng SBC (ADI 1.32, CV² 0.49). Trái-dưới: đều · trái-trên: thất thường · "
             "phải-dưới: ngắt quãng · phải-trên: cục", ha="center", color=MUTED, fontsize=8.5)
    save(fig, out, "1b_sbc")

    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    s = res["category_spend_share"]
    ax.barh(list(s)[::-1], list(s.values())[::-1], color=C[0], height=0.6)
    ax.set_xlabel("tỷ trọng tổng chi")
    ax.set_title("Cơ cấu chi theo danh mục AssistAI")
    ax.grid(axis="y", visible=False)
    save(fig, out, "1c_category_share")
    return res


# ---------------------------------------------------------------- 2. calendar

def calendar_effects(daily, ids, out):
    res = {}
    d = daily.assign(norm=daily["y"] / daily.groupby("unique_id")["y"].transform("mean"))
    d = d[np.isfinite(d["norm"])]
    dow = d["ds"].dt.dayofweek
    prof = d.groupby(dow)["norm"].agg(["mean", "sem"])
    res["dow_mean"] = dict(zip(DOW, prof["mean"]))
    groups = [g.to_numpy() for _, g in d.groupby(dow)["norm"]]
    H, p = stats.kruskal(*groups)
    res["dow_kruskal"] = {"H": H, "p": p, "epsilon2": H / (len(d) - 1)}
    frac = []
    for uid in ids:
        g = d[d["unique_id"] == uid]
        frac.append(stats.kruskal(*[x.to_numpy() for _, x in g.groupby(g["ds"].dt.dayofweek)["norm"]]).pvalue < 0.05)
    res["dow_kruskal_user_sig_share"] = float(np.mean(frac))

    dom = d.groupby(d["ds"].dt.day)["norm"].mean()
    res["dom_mean"] = dom.to_dict()
    res["dom_first5_vs_rest"] = dom.loc[1:5].mean() / dom.loc[6:28].mean()

    m = monthly_table(daily)
    full = daily.assign(month=daily["ds"].dt.to_period("M"))
    mm = full.groupby(["unique_id", "month"]).agg(S=("y", "sum"), n=("y", "size")).reset_index()
    mm = mm[mm["n"] == mm["month"].dt.days_in_month]
    mm["rel"] = mm["S"] / mm.groupby("unique_id")["S"].transform("mean")
    moy = mm.groupby(mm["month"].dt.month)["rel"].mean()
    res["moy_mean"] = moy.to_dict()

    # Đường chi tích lũy S(d)/S(N) — nếu chi đều thì nằm trên đường chéo d/N
    dd = d.assign(month=d["ds"].dt.to_period("M").astype(str), day=d["ds"].dt.day)
    dd["S"] = dd.groupby(["unique_id", "month"])["y"].cumsum()
    dd = dd.merge(m[["unique_id", "month", "S_N", "N"]], on=["unique_id", "month"])
    dd = dd[dd["S_N"] > 0]
    dd["share"] = dd["S"] / dd["S_N"]
    q = dd.groupby("day")["share"].quantile([0.1, 0.5, 0.9]).unstack()
    lin = dd.groupby("day")["N"].mean()
    res["cum_share"] = {int(k): {"p10": q.loc[k, 0.1], "median": q.loc[k, 0.5], "p90": q.loc[k, 0.9],
                                 "linear": k / lin.loc[k]} for k in (5, 10, 15, 20, 25)}

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.4), gridspec_kw={"width_ratios": [1, 2, 1.4]})
    axes[0].bar(DOW, prof["mean"], yerr=1.96 * prof["sem"], color=C[0], width=0.6, ecolor=MUTED)
    axes[0].set_title("Theo thứ trong tuần")
    axes[0].set_ylabel("chi ÷ TB của user")
    axes[1].bar(dom.index, dom.values, color=C[0], width=0.7)
    axes[1].set_title("Theo ngày trong tháng (chi/ngày)")
    axes[2].bar(moy.index, moy.values, color=C[0], width=0.7)
    axes[2].set_xticks(range(1, 13))
    axes[2].set_title("Theo tháng (tổng tháng)")
    for ax in axes:
        ax.axhline(1, color=MUTED, lw=1)
        ax.grid(axis="x", visible=False)
    save(fig, out, "2a_calendar")

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.fill_between(q.index, q[0.1], q[0.9], color=C[0], alpha=0.18, linewidth=0, label="10%–90% số tháng")
    ax.plot(q.index, q[0.5], color=C[0], label="trung vị")
    ax.plot(lin.index, lin.index / lin.values, color=MUTED, ls="--", lw=1.5, label="chi đều (d/N)")
    ax.set_xlabel("ngày trong tháng d")
    ax.set_ylabel("S(d) / S(N)")
    ax.set_title("Tỷ lệ đã chi đến ngày d so với cả tháng")
    ax.legend(loc="upper left")
    save(fig, out, "2b_cumulative_share")
    return res


# ---------------------------------------------------------------- 3. stationarity

def _adf_kpss(x):
    x = np.asarray(x, dtype=float)
    if len(x) < 20 or np.std(x) == 0:
        return None
    pa = adfuller(x, autolag="AIC")[1]
    pk = kpss(x, regression="c", nlags="auto")[1]
    if pa < 0.05 and pk >= 0.05:
        return "dừng"
    if pa >= 0.05 and pk < 0.05:
        return "có nghiệm đơn vị"
    if pa < 0.05 and pk < 0.05:
        return "dừng quanh xu hướng / cấu trúc thay đổi"
    return "không kết luận"


def stationarity(daily, ids):
    res = {}
    rows = {"ngày (log1p)": [], "tuần": [], "tháng": []}
    for uid in ids:
        s = daily[daily["unique_id"] == uid].set_index("ds")["y"]
        rows["ngày (log1p)"].append(_adf_kpss(np.log1p(s)))
        rows["tuần"].append(_adf_kpss(s.resample("W").sum().iloc[1:-1]))
        mo = s.resample("MS").sum().iloc[1:-1]
        rows["tháng"].append(_adf_kpss(mo) if len(mo) >= 24 else None)
    for k, v in rows.items():
        v = pd.Series([x for x in v if x is not None])
        res[k] = {"n": int(len(v)), **v.value_counts(normalize=True).to_dict()} if len(v) else {"n": 0}
    return res


# ---------------------------------------------------------------- 4. dependence

def dependence(daily, ids, out):
    res = {}
    acfs, pacfs, lb, lb_res, Fs, Ft, p_aic, p_bic, stl_keep = [], [], [], [], [], [], [], [], {}
    for uid in ids:
        s = daily[daily["unique_id"] == uid].set_index("ds")["y"]
        x = np.log1p(s)
        if len(x) < 120 or x.std() == 0:  # cần ≥ 120 ngày cho ACF/PACF đến trễ 35
            continue
        acfs.append(acf(x, nlags=35, fft=True))
        pacfs.append(pacf(x, nlags=35))
        lb.append(acorr_ljungbox(x, lags=[7, 14, 28])["lb_pvalue"].to_numpy())
        resid = x - x.groupby(x.index.dayofweek).transform("mean")  # bỏ mùa vụ theo thứ
        lb_res.append(acorr_ljungbox(resid, lags=[7, 14, 28])["lb_pvalue"].to_numpy())
        r = STL(x.to_numpy(), period=7, robust=True).fit()
        Fs.append(max(0, 1 - np.var(r.resid) / np.var(r.seasonal + r.resid)))
        Ft.append(max(0, 1 - np.var(r.resid) / np.var(r.trend + r.resid)))
        stl_keep[uid] = (x, r)
        for ic, store in (("aic", p_aic), ("bic", p_bic)):
            sel = ar_select_order(x.to_numpy(), maxlag=14, ic=ic, trend="c")
            store.append(max(sel.ar_lags) if sel.ar_lags else 0)
    acfs, pacfs, lb, lb_res = map(np.array, (acfs, pacfs, lb, lb_res))
    n_obs = daily.groupby("unique_id").size().loc[list(stl_keep)].mean()
    band = 1.96 / np.sqrt(n_obs)
    res["acf_mean"] = {k: acfs[:, k].mean() for k in (1, 2, 3, 7, 14, 21, 28)}
    res["pacf_mean"] = {k: pacfs[:, k].mean() for k in (1, 2, 3, 7, 14)}
    res["white_noise_band"] = band
    res["acf_sig_share"] = {k: float(np.mean(np.abs(acfs[:, k]) > band)) for k in (1, 7, 14)}
    res["ljungbox_sig_share"] = dict(zip(["lag7", "lag14", "lag28"], (lb < 0.05).mean(0)))
    res["ljungbox_sig_share_after_dow"] = dict(zip(["lag7", "lag14", "lag28"], (lb_res < 0.05).mean(0)))
    res["ljungbox_p_median"] = dict(zip(["lag7", "lag14", "lag28"], np.median(lb, 0)))
    res["stl_seasonal_strength"] = desc(Fs)
    res["stl_trend_strength"] = desc(Ft)
    res["ar_order_aic"] = desc(p_aic)
    res["ar_order_bic"] = desc(p_bic)
    res["ar_order_bic_dist"] = pd.Series(p_bic).value_counts(normalize=True).sort_index().to_dict()

    lags = np.arange(36)
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.4), sharey=True)
    for ax, arr, ttl in [(axes[0], acfs, "ACF log(1+chi/ngày)"), (axes[1], pacfs, "PACF log(1+chi/ngày)")]:
        ax.axhspan(-band, band, color=MUTED, alpha=0.12, label="vùng nhiễu trắng 95%")
        if len(arr) > 1:
            lo, hi = np.percentile(arr, [10, 90], axis=0)
            ax.fill_between(lags[1:], lo[1:], hi[1:], color=C[0], alpha=0.18, linewidth=0, label="10%–90% user")
        ax.bar(lags[1:], arr.mean(0)[1:], color=C[0], width=0.6, label="trung bình" if len(arr) > 1 else "giá trị")
        ax.set_xlabel("độ trễ (ngày)")
        ax.set_title(ttl)
        ax.set_xticks([1, 7, 14, 21, 28, 35])
    axes[0].legend(loc="upper right", fontsize=8)
    save(fig, out, "4a_acf_pacf")

    # STL của user có độ mạnh mùa vụ ở mức trung vị, 140 ngày cuối
    uid = list(stl_keep)[int(np.argsort(Fs)[len(Fs) // 2])]
    x, r = stl_keep[uid]
    sl = slice(-140, None)
    fig, axes = plt.subplots(4, 1, figsize=(9, 6), sharex=True)
    for ax, v, ttl in zip(axes, [x.to_numpy(), r.trend, r.seasonal, r.resid], ["log(1+y)", "xu hướng", "mùa vụ 7 ngày", "phần dư"]):
        ax.plot(x.index[sl], v[sl], color=C[0], lw=1.4)
        ax.set_ylabel(ttl, fontsize=9)
    axes[0].set_title(f"Phân rã STL — user có độ mạnh mùa vụ trung vị (F_s = {np.median(Fs):.2f})")
    save(fig, out, "4b_stl")

    # Phụ thuộc giữa các tháng: độ lệch của tổng tháng so với TB của user
    full = daily.assign(month=daily["ds"].dt.to_period("M"))
    mm = full.groupby(["unique_id", "month"]).agg(S=("y", "sum"), n=("y", "size")).reset_index()
    mm = mm[mm["n"] == mm["month"].dt.days_in_month].sort_values(["unique_id", "month"]).reset_index(drop=True)
    mm["dev"] = mm["S"] / mm.groupby("unique_id")["S"].transform("mean") - 1
    res["monthly_autocorr"] = {}
    for k in (1, 2, 3, 12):
        prev = mm.groupby("unique_id")["dev"].shift(k)
        ok = prev.notna() & (mm.groupby("unique_id")["month"].shift(k) == mm["month"] - k)
        if ok.sum() > 10:
            rho, p = stats.spearmanr(mm["dev"][ok], prev[ok])
            res["monthly_autocorr"][f"lag{k}"] = {"spearman": rho, "p": p, "n": int(ok.sum())}
    res["monthly_cv"] = desc(mm.groupby("unique_id")["S"].agg(lambda s: s.std() / s.mean()))
    return res


# ---------------------------------------------------------------- 5. categories

def categories(catd, out):
    res = {}
    cats = sorted({c for p in catd.values() for c in p.columns},
                  key=lambda c: -sum(p[c].sum() for p in catd.values() if c in p))
    top = cats[:8]

    # Tương quan Spearman giữa danh mục theo tuần, trung bình qua user
    mats = []
    for p in catd.values():
        w = p.resample("W").sum().iloc[1:-1].reindex(columns=top)
        if len(w) >= 10:
            mats.append(w.corr(method="spearman").to_numpy())
    R = np.nanmean(np.array(mats), axis=0)
    res["weekly_corr"] = pd.DataFrame(R, index=top, columns=top).to_dict()
    off = R[~np.eye(len(top), dtype=bool)]
    res["weekly_corr_offdiag"] = {"mean": np.nanmean(off), "max": np.nanmax(off), "min": np.nanmin(off)}

    # Đóng góp phương sai vào tổng tháng: cov(danh mục, tổng)/var(tổng), cộng lại = 1
    contrib = []
    for p in catd.values():
        mo = p.resample("MS").sum()
        n = p.resample("MS").size()
        mo = mo[(n == mo.index.days_in_month).to_numpy()]
        if len(mo) < 6:
            continue
        T = mo.sum(1)
        if T.var() == 0:
            continue
        contrib.append({c: np.cov(mo[c], T)[0, 1] / T.var() for c in mo.columns})
    res["var_contrib"] = pd.DataFrame(contrib).fillna(0).mean().sort_values(ascending=False).to_dict()

    # Granger theo ngày, độ trễ cố định 7: chi danh mục A có giúp dự báo B không
    g4 = cats[:4]
    gr = {}
    for a in g4:
        for b in g4:
            if a == b:
                continue
            ps = []
            for p in list(catd.values())[:150]:
                if a not in p or b not in p or p[a].std() == 0 or p[b].std() == 0:
                    continue
                X = np.log1p(p[[b, a]].to_numpy())
                try:
                    with contextlib.redirect_stdout(io.StringIO()):
                        r = grangercausalitytests(X, maxlag=[7])
                    ps.append(r[7][0]["ssr_ftest"][1])
                except Exception:
                    pass
            if ps:
                gr[f"{a} → {b}"] = {"sig_share": float(np.mean(np.array(ps) < 0.05)), "median_p": float(np.median(ps)), "n": len(ps)}
    res["granger_lag7"] = gr

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.4), gridspec_kw={"width_ratios": [1.15, 1]})
    vmax = max(0.3, float(np.nanmax(np.abs(off))))
    im = axes[0].imshow(np.where(np.eye(len(top), dtype=bool), np.nan, R), cmap=DIVERGING, vmin=-vmax, vmax=vmax)
    axes[0].set_xticks(range(len(top)), top, rotation=45, ha="right", fontsize=8)
    axes[0].set_yticks(range(len(top)), top, fontsize=8)
    for i in range(len(top)):
        for j in range(len(top)):
            if i != j and np.isfinite(R[i, j]):
                axes[0].text(j, i, f"{R[i, j]:.2f}", ha="center", va="center", fontsize=7, color=INK)
    axes[0].grid(False)
    axes[0].set_title("Tương quan Spearman chi theo tuần")
    fig.colorbar(im, ax=axes[0], shrink=0.8)
    vc = pd.Series(res["var_contrib"]).head(10)
    axes[1].barh(vc.index[::-1], vc.values[::-1], color=C[0], height=0.6)
    axes[1].axvline(0, color=MUTED, lw=1)
    axes[1].set_title("Đóng góp vào phương sai tổng chi tháng")
    axes[1].grid(axis="y", visible=False)
    save(fig, out, "5a_category_dependence")
    return res


# ---------------------------------------------------------------- 6. features

def features(name, daily, out):
    res = {}
    days = [5, 10, 15, 20, 25]
    dl = daily.copy()
    dl["pos"] = dl.groupby("unique_id").cumcount()
    dl["cs"] = dl.groupby("unique_id")["y"].cumsum()
    for h in (3, 7, 14, 28):
        dl[f"ewm{h}"] = dl.groupby("unique_id")["y"].transform(lambda s, h=h: s.ewm(halflife=h).mean())
    ef = eval_frame(name, daily, days=days)
    ef = ef[ef["split"] == "train"].merge(dl[["unique_id", "ds", "pos", "cs"] + [f"ewm{h}" for h in (3, 7, 14, 28)]],
                                          left_on=["unique_id", "origin"], right_on=["unique_id", "ds"]).reset_index(drop=True)
    key = dl.set_index(["unique_id", "pos"])
    rem_days = (ef["N"] - ef["d"]).to_numpy()
    target = (ef["S_N"] - ef["S_d"]) / ef["scale"]
    res["n_origins"] = int(len(ef))

    def lag_y(j):
        idx = pd.MultiIndex.from_arrays([ef["unique_id"], ef["pos"] - j])
        return key["y"].reindex(idx).to_numpy()

    def roll_mean(k):
        """TB k ngày gần nhất tính đến hết ngày d (thiếu lịch sử thì dùng số ngày đang có)."""
        idx = pd.MultiIndex.from_arrays([ef["unique_id"], ef["pos"] - k])
        prev = key["cs"].reindex(idx).to_numpy()
        n = np.where(np.isnan(prev), ef["pos"] + 1, k)
        return (ef["cs"].to_numpy() - np.nan_to_num(prev)) / n

    # 6a. Độ dài cửa sổ: phần còn lại = (TB k ngày gần nhất) × số ngày còn lại
    preds = {"runrate (trong tháng)": ef["S_d"] / ef["d"]}
    for k in (3, 7, 14, 21, 28, 42, 56, 91):
        preds[f"MA{k}"] = roll_mean(k)
    for h in (3, 7, 14, 28):
        preds[f"EWMA hl={h}"] = ef[f"ewm{h}"]
    preds["TB 3 tháng trước"] = ef["scale"] / ef["N"]
    yN, dcol = ef["S_N"].to_numpy(), ef["d"].to_numpy()
    win = {}
    for k, v in preds.items():
        err = np.abs(yN - (ef["S_d"].to_numpy() + np.asarray(v, dtype=float) * rem_days))
        win[k] = {"WAPE": err.sum() / yN.sum(), **{f"d{d}": err[dcol == d].sum() / yN[dcol == d].sum() for d in days}}
    res["window_wape"] = win

    # 6b. Spearman feature – mục tiêu (phần còn lại / thang đo), tính riêng từng d rồi lấy TB
    s = ef["scale"]
    F = pd.DataFrame({
        "S_d (đã chi)": ef["S_d"] / s, "runrate": ef["S_d"] / ef["d"] * ef["N"] / s,
        **{f"MA{k}": roll_mean(k) / s for k in (7, 14, 28, 56)},
        **{f"EWMA{h}": ef[f"ewm{h}"] / s for h in (7, 28)},
        **{f"lag{j}": lag_y(j) / s for j in (0, 1, 2, 7)},
        "prev1 (tháng trước)": ef["prev1"] / s, "B (trung vị 3T)": ef["B"] / s,
        "dow (thứ của ngày d)": ef["origin"].dt.dayofweek,
    })
    groups = {"S_d (đã chi)": "tích lũy trong tháng", "runrate": "tích lũy trong tháng",
              "prev1 (tháng trước)": "lịch sử tháng", "B (trung vị 3T)": "lịch sử tháng", "dow (thứ của ngày d)": "lịch"}
    corr = {}
    for c in F.columns:
        rs = [stats.spearmanr(F[c][dcol == d], target[dcol == d], nan_policy="omit")[0] for d in days]
        corr[c] = {"mean_rho": float(np.nanmean(rs)), **{f"d{d}": float(r) for d, r in zip(days, rs)}}
    res["feature_spearman"] = corr

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.4), gridspec_kw={"width_ratios": [1.1, 1]})
    w = pd.Series({k: v["WAPE"] for k, v in win.items()})
    kind = lambda k: "trong tháng" if k.startswith("runrate") else "lịch sử tháng" if k.startswith("TB") else "MA (cửa sổ trượt)" if k.startswith("MA") else "EWMA"
    kcol = {"trong tháng": C[1], "lịch sử tháng": C[2], "MA (cửa sổ trượt)": C[0], "EWMA": C[6]}
    axes[0].barh(w.index[::-1], w.values[::-1], color=[kcol[kind(k)] for k in w.index[::-1]], height=0.6)
    axes[0].set_xlabel("WAPE tổng chi tháng (train, d = 5…25)")
    axes[0].set_title("Chọn cửa sổ: TB k ngày × số ngày còn lại")
    axes[0].grid(axis="y", visible=False)
    axes[0].legend(handles=[Patch(color=v, label=k) for k, v in kcol.items()], loc="upper center",
                   bbox_to_anchor=(0.5, -0.16), ncol=4, fontsize=8)
    cs = pd.Series({k: v["mean_rho"] for k, v in corr.items()}).sort_values()
    grp = [groups.get(k, "trễ (AR)" if k.startswith("lag") else "rolling / MA / EWMA") for k in cs.index]
    gcol = {"tích lũy trong tháng": C[1], "lịch sử tháng": C[2], "lịch": C[3], "trễ (AR)": C[6], "rolling / MA / EWMA": C[0]}
    axes[1].barh(cs.index, cs.values, color=[gcol[g] for g in grp], height=0.6)
    axes[1].axvline(0, color=MUTED, lw=1)
    axes[1].set_xlabel("Spearman ρ với phần chi còn lại (TB qua d)")
    axes[1].set_title("Tương quan feature – mục tiêu")
    axes[1].grid(axis="y", visible=False)
    axes[1].legend(handles=[Patch(color=v, label=k) for k, v in gcol.items()], loc="upper center",
                   bbox_to_anchor=(0.5, -0.16), ncol=3, fontsize=8)
    save(fig, out, "6a_features")
    return res


def to_jsonable(o):
    if isinstance(o, dict):
        return {str(k): to_jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [to_jsonable(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not np.isfinite(o) else round(float(o), 4)
    if isinstance(o, np.integer):
        return int(o)
    return o


def main(name, n_sample=300, only=None):
    out = ROOT / "eda" / name
    out.mkdir(parents=True, exist_ok=True)
    tx = load_transactions(name)
    daily = load_daily(name)
    uids = daily["unique_id"].unique()
    rng = np.random.default_rng(0)
    ids = list(rng.choice(uids, size=min(n_sample, len(uids)), replace=False))
    catd = cat_daily(tx[(tx["amount"] > 0) & ~tx["fraud"]], ids)
    path = out / "stats.json"
    res = json.loads(path.read_text(encoding="utf-8")) if (only and path.exists()) else {}
    res.update({"dataset": name, "n_sample_users": len(ids)})
    steps = [("profile", lambda: profile(tx, daily, catd, out)),
             ("calendar", lambda: calendar_effects(daily, ids, out)),
             ("stationarity", lambda: stationarity(daily, ids)),
             ("dependence", lambda: dependence(daily, ids, out)),
             ("categories", lambda: categories(catd, out)),
             ("features", lambda: features(name, daily, out))]
    for key, fn in steps:
        if only and key not in only:
            continue
        print(f"[{name}] {key} …", flush=True)
        res[key] = fn()
        path.write_text(json.dumps(to_jsonable(res), ensure_ascii=False, indent=1), encoding="utf-8")
    print("xong →", out)


if __name__ == "__main__":
    args = sys.argv[1:]
    only = [a for a in args[1:] if not a.isdigit()] or None
    n = next((int(a) for a in args[1:] if a.isdigit()), 300)
    main(args[0], n, only)
