# -*- coding: utf-8 -*-
"""exposure_timing.py —— 暴露时点与新发敏感性（lag-2 与仅新发 MASLD）

规格先冻：the prespecified analysis specification, frozen before the analysis.
风险集/协变量/拟合器与 version_contrast_run.py build()+fit_fe() 逐字同源；运行时对 primary 锚做 fail-loud
断言（= 既存规格网格锚：HR 0.964 (0.9236–1.0061)，n=46,973，14,656 events），锚不符即退出。

三个规格（同一 primary 风险集：前波 ECG 正常 + 间隔≤2 年 + 完整病例）：
  primary   暴露 = 前波 masld（shift(1)）                              —— 锚复现，不改任何值
  lag2      暴露 = 前两记录位 masld（shift(2)，同一子集基准）          —— 须 t−2 记录存在且间隔 ≤4 年
  incident  暴露 = 前波 masld 不变；风险集追加「t−2 及更早波均无 MASLD」
            ⇒ 暴露行均为前一波新发；现患暴露者整行退出风险集（非重编码为 0）

输入：analysis_frame.csv（study data root 定稿帧）+ 文本结局缓存（EXPOSURE_TIMING_CACHE 指认，通常 = 主分析的
outcome_cache_v3.csv.gz；the text domain is unchanged in the production freeze, so the cache remains valid）。缓存缺失时与主分析同法现场重算
（from main import extract_ecg, norm）。
输出：exposure_timing_sensitivity.csv + _summary.txt（EXPOSURE_TIMING_RES，默认本侧 results/）
用法：EXPOSURE_TIMING_CACHE=<cache> [EXPOSURE_TIMING_RES=<dir>] python exposure_timing.py
"""
import os
import sys
import time

import numpy as np
import pandas as pd
from lifelines import CoxPHFitter

ROOT = r"STUDY_ROOT"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.environ.get("EXPOSURE_TIMING_RES", os.path.join(HERE, "results"))
STUDY_ROOT = r"study-data-root"
# EXPOSURE_TIMING_FRAME：分析帧。默认 = 主分析定稿帧 analysis_frame_production_freeze.csv（primary 锚 n=46,973 所出之帧）。
# ⚠ 不可用 live 帧：processed\analysis_frame.csv 已于 2026-10-24 随数据层 v1.2 重构（mtime 实测），
# 其 HARM 缺失模式与主分析运行时（2026-09-20）不同 ⇒ dropna 后风险集漂移（实测 49,559≠46,973）。
FRAME_PATH = os.environ.get(
    "EXPOSURE_TIMING_FRAME",
    os.path.join(STUDY_ROOT, "data", "processed", "analysis_frame_production_freeze.csv"))
HARM = ["sii_q", "proteinuria", "bmi", "htn_screen", "dm_screen"]
SEED_ANCHOR = {"HR": 0.964, "lo": 0.9236, "hi": 1.0061, "n": 46973, "events": 14656}
os.makedirs(RES, exist_ok=True)
rep = []

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def rl(s=""):
    print(s, flush=True)
    rep.append(str(s))


t0 = time.time()
rl("=== 暴露时点与新发敏感性（lag-2 / 仅新发 MASLD）===")
FRAME = pd.read_csv(FRAME_PATH,
                    encoding="utf-8-sig", dtype={"id": str, "ecg_text": str}, low_memory=False)
FRAME = FRAME.sort_values(["id", "year"]).reset_index(drop=True)
rl(f"帧载入: {len(FRAME):,} 行, {FRAME['id'].nunique():,} 人（{time.time() - t0:.0f}s）")

CACHE = os.environ.get("EXPOSURE_TIMING_CACHE", os.path.join(RES, "outcome_cache_v3.csv.gz"))
if os.path.exists(CACHE):
    c = pd.read_csv(CACHE, encoding="utf-8-sig")
    if len(c) == len(FRAME):
        FRAME["v1_abnormal"], FRAME["v3_abnormal"] = c["v1_abnormal"].to_numpy(), c["v3_abnormal"].to_numpy()
        rl("v1/v3 结局列：自缓存载入（%s）" % os.path.basename(CACHE))
    else:
        c = None
else:
    c = None
if c is None or len(c) != len(FRAME):
    sys.path.insert(0, os.path.join(ROOT, "code")); sys.path.insert(0, HERE)  # deposited main.py in this package takes precedence
    from main import extract_ecg, norm  # noqa: E402
    m = FRAME["ecg_text"].notna()
    v3 = pd.DataFrame(FRAME.loc[m, "ecg_text"].map(lambda t: extract_ecg(norm(t))).tolist())
    for col in v3.columns:
        FRAME.loc[m, "v3_" + col] = v3[col].values
    FRAME["v3_abnormal"] = ((FRAME["v3_ecg_normal"] == 0) & (FRAME["v3_ecg_unreadable"] == 0)).astype(float)
    FRAME.loc[~m, "v3_abnormal"] = np.nan
    FRAME["v1_abnormal"] = FRAME["ecg_abnormal"].astype(float)
    rl("v1/v3 结局列：现场重算（未写缓存，EXPOSURE_TIMING_RES 不落缓存）")
ECGDF = FRAME[FRAME["v1_abnormal"].notna() | FRAME["v3_abnormal"].notna()].copy()


def build(outkey, covs, yfe, mode="primary"):
    """与 version_contrast_run.build() 逐字同源；mode 追加两个敏感性变体（shift 均在子集内、过滤前）。"""
    g = ECGDF.sort_values(["id", "year"]).copy()
    g["_prev_y"] = g.groupby("id")[outkey].shift()
    g["_prev_t"] = g.groupby("id")["year"].shift()
    for cc in ["age", "sex_male", "masld"] + covs:
        g[cc] = g.groupby("id")[cc].shift()
    g = g.rename(columns={"age": "p_age", "sex_male": "p_male"})
    g["_m2"] = g.groupby("id")["masld"].shift(2)                       # 前两记录位 masld
    g["_t2"] = g.groupby("id")["year"].shift(2)
    g["_mhist"] = g.groupby("id")["masld"].shift(2).groupby(g["id"]).cummax()  # t−2 及更早波 MASLD 史
    keep = g["_prev_y"].notna() & g[outkey].notna() & ((g["year"] - g["_prev_t"]) <= 2)
    g = g[keep & (g["_prev_y"] == 0)].copy()
    gap_med = None
    if mode == "lag2":
        g["_gap2"] = g["year"] - g["_t2"]
        g = g[g["_m2"].notna() & (g["_gap2"] <= 4)].copy()
        gap_med = float(g["_gap2"].median())
        g["masld"] = g["_m2"]
    elif mode == "incident":
        g = g[g["_mhist"].isna() | (g["_mhist"] == 0)].copy()          # 前波之前无 MASLD 史 ⇒ 暴露=新发
    g["event"] = g[outkey].astype(int)
    covs_all = ["p_age", "p_male", "masld"] + covs
    if yfe:
        yd = pd.get_dummies(g["year"].astype(int), prefix="y", drop_first=True).astype(float)
        g = pd.concat([g, yd], axis=1)
        covs_all = covs_all + list(yd.columns)
    g = g.dropna(subset=covs_all)
    return g, covs_all, gap_med


def fit_fe(g, covs_all, penalizer=0.01):
    g = g.copy()
    g["T"] = 1.0
    cph = CoxPHFitter(penalizer=penalizer)
    cph.fit(g[["T", "event"] + list(covs_all) + ["id"]],
            duration_col="T", event_col="event", cluster_col="id", show_progress=False)
    return cph


def hr_of(model, term="masld"):
    s = model.summary.loc[term]
    return (float(s["exp(coef)"]), float(s["exp(coef) lower 95%"]),
            float(s["exp(coef) upper 95%"]), float(s["p"]))


rows = []
for spec, mode, note in [
    ("primary", "primary", "exposure = prior-wave MASLD (lag 1); identical to the locked primary estimand (anchor)"),
    ("lag2", "lag2", "exposure = MASLD two records earlier (complete-case on the t-2 record; gap to t-2 <= 4 years); covariates and risk set unchanged"),
    ("incident", "incident", "risk set restricted to records with no MASLD at or before t-2, so every exposed record is newly diagnosed MASLD in the preceding wave; prevalent exposure exits the risk set (not recoded)"),
]:
    g, covs_all, gap_med = build("v3_abnormal", HARM, True, mode=mode)
    m = fit_fe(g, covs_all)
    hr, lo, hi, pv = hr_of(m)
    rl(f"  {spec:9s} HR={hr:.4f} ({lo:.4f}–{hi:.4f})  p={pv:.4f}  n={len(g):,} ev={int(g['event'].sum()):,}"
       + (f"  gap_med={gap_med}" if gap_med is not None else ""))
    if spec == "primary":
        ok = (round(hr, 4) == SEED_ANCHOR["HR"] and round(lo, 4) == SEED_ANCHOR["lo"]
              and round(hi, 4) == SEED_ANCHOR["hi"] and len(g) == SEED_ANCHOR["n"]
              and int(g["event"].sum()) == SEED_ANCHOR["events"])
        if not ok:
            sys.exit("FAIL: primary 锚与既有规格网格不符（fail-loud）——禁止产出")
        rl("  primary 锚与既有规格网格逐位相符（0.964/0.9236/1.0061/46,973/14,656）⇒ 机器可信")
    n_note = note + (f" Median gap to the t-2 record: {gap_med:.0f} years." if gap_med is not None else "")
    rows.append({"spec": spec, "HR": round(hr, 4), "lo": round(lo, 4), "hi": round(hi, 4),
                 "p": round(pv, 4), "n_risk": len(g), "n_events": int(g["event"].sum()),
                 "exposure_note": n_note})

import csv as _csv
out_csv = os.path.join(RES, "exposure_timing_sensitivity.csv")
with open(out_csv, "w", encoding="utf-8-sig", newline="") as f:
    w = _csv.DictWriter(f, fieldnames=["spec", "HR", "lo", "hi", "p", "n_risk", "n_events", "exposure_note"])
    w.writeheader()
    w.writerows(rows)
with open(os.path.join(RES, "exposure_timing_summary.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rep) + "\n")
rl(f"\nWROTE {out_csv}")
rl(f"DONE（{time.time() - t0:.0f}s）")
