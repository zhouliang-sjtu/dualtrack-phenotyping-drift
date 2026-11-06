# -*- coding: utf-8 -*-
"""a5_drift_dose_response.py —— drift 剂量-反应 stress test（真实漂移材料，文本级）

设计（对导师 spec 的忠实实现，材料学上更保守）：
  基线 = 2021 稳定年全部非空 ECG 文本（主分析帧）；漂移材料 = 真实 2023 记录（携带实际发生的三类
  文档漂移形态：结论稀疏化/模板枚举混入/定义混杂——不做人工合成扰动，保真度更高）。
  剂量 d ∈ {0,5,10,20,30,50}%：自 2023 无放回抽取 d×n_2021 条替换进基线（seed 20260921）。
  每剂量测量：
    ① naive(v3_A) 患病率 vs 显式(v3_B) 患病率 → prevalence distortion (pp)
    ② naive-vs-explicit 分歧核 /1000（表型误分类负担代理，效度由 A2/160 条裁定集人体实测背书）
    ③ 监测器信号：v1×v3 一致性 κ + 4 项风格信号，对 2018–2022 基线（median/MAD）做稳健 z，
       报警规则同主分析（≥2 信号 |z|>3）——回答"监测器能否随剂量预警"。
  全部 flags 用冻结管线既有产物（v3=缓存、v1=生产列），不重新调参。
输出：results/wp1_drift_dose_response.csv + summary txt
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = r"STUDY_ROOT"
STUDY_ROOT = r"study-data-root"
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "results")
SEED = 20260921
# 原网格止于 50%，外部评审要求补 40% 与 60–100%。漂移池 21,625 ≥ 基线 15,576，
# 100% 可无放回构造；100% 端点 = 纯 2023 样本，应复现实测 2023 畸变 −14·82 pp（设计自校验）。
DOSES = [0, 5, 10, 20, 30, 40, 50, 60, 80, 100]

sys.path.insert(0, os.path.join(ROOT, "code")); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # deposited main.py in this package takes precedence
from main import norm  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

rep = []


def rl(s=""):
    print(s, flush=True)
    rep.append(str(s))


rl("=== drift dose-response（真实 2023 材料 × 2021 基线）===")

d = pd.read_csv(os.path.join(STUDY_ROOT, "data", "processed", "analysis_frame.csv"),
                encoding="utf-8-sig", dtype={"id": str, "ecg_text": str}, low_memory=False)
d = d.sort_values(["id", "year"]).reset_index(drop=True)
c = pd.read_csv(os.path.join(RES, "v3_flags_cache.csv.gz"), encoding="utf-8-sig")
for col in c.columns:
    d[col] = c[col].to_numpy()
d["t"] = d["ecg_text"].fillna("").map(norm)
d = d[d["t"] != ""].copy()

ENUM = ["v3_ecg_af", "v3_ecg_pac_pvc", "v3_ecg_stt", "v3_ecg_rate", "v3_ecg_srirr",
        "v3_ecg_axis", "v3_ecg_qwave_mi"]
A = ((pd.to_numeric(d["v3_ecg_normal"], errors="coerce") == 0) &
     (pd.to_numeric(d["v3_ecg_unreadable"], errors="coerce") == 0)).astype(float)
Bx = ((d[ENUM].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1) > 0) |
      (pd.to_numeric(d["v3_ecg_avblock"], errors="coerce").fillna(0) +
       pd.to_numeric(d["v3_ecg_bbb"], errors="coerce").fillna(0) > 0)).astype(float)
d["_A"], d["_B"] = A, Bx
d["_v1abn"] = pd.to_numeric(d["ecg_abnormal"], errors="coerce")

base = d[d["year"].astype(str) == "2021"].reset_index(drop=True)
drift_pool = d[d["year"].astype(str) == "2023"].reset_index(drop=True)
rl(f"基线 2021：{len(base):,}；漂移材料 2023：{len(drift_pool):,}")

# S 基线参数（2018–2022，median/MAD）——报警 z 的参照
sig = pd.read_csv(os.path.join(RES, "drift_monitor_signals.csv"), encoding="utf-8-sig")
bl = sig[sig["year"] <= 2022]
SIGNALS = ["agreement_pct", "kappa_v1v3", "posrate_v1", "posrate_v3",
           "median_len", "inline_enum_pct", "domain_mix_pct", "ecg_prefix_pct"]


def robust_z(x, med, mad):
    return 0.0 if mad == 0 else (x - med) / (1.4826 * mad)


def mixed_dose(ddose):
    rng = np.random.default_rng(SEED + ddose)
    n_drift = int(round(len(base) * ddose / 100))
    take = rng.choice(len(drift_pool), size=n_drift, replace=False)
    keep = rng.choice(len(base), size=len(base) - n_drift, replace=False)
    return pd.concat([base.iloc[keep], drift_pool.iloc[take]], ignore_index=True), n_drift


def signals_of(m):
    t = m["t"]
    agree = float(np.mean(m["_A"] == m["_B"])) * 100 if m["_A"].notna().all() else np.nan
    # v1×v3 κ
    v1, v3 = m["_v1abn"].to_numpy(), m["_A"].to_numpy()
    ok = ~(pd.isna(v1) | pd.isna(v3))
    labs = [0.0, 1.0]
    po = float(np.mean(v1[ok] == v3[ok]))
    pe = sum(float(np.mean(v1[ok] == L)) * float(np.mean(v3[ok] == L)) for L in labs)
    k = (po - pe) / (1 - pe) if pe < 1 else 1.0
    return {
        "agreement_pct": agree,
        "kappa_v1v3": k,
        "posrate_v1": float(np.nanmean(v1[ok])) * 100,
        "posrate_v3": float(np.nanmean(m["_A"].to_numpy())) * 100,
        "median_len": float(np.median([len(x) for x in t])),
        "inline_enum_pct": float(np.mean([("、" in x) for x in t])) * 100,
        "domain_mix_pct": float(np.mean([bool(__import__("re").search(r"肝|胆|脾|肾", x)) for x in t])) * 100,
        "ecg_prefix_pct": float(np.mean([x.startswith("心电图") for x in t])) * 100,
    }


# z(enumeration) 在所有剂量点为负，须给出可复核的方向成因与量纲。
# 该 z 由 inline_enum_pct 对 2018–2022 median/MAD 做稳健标准化得到；把三方实测值落盘，
# 使「负号来自基线量级而非报警逻辑错误」可被独立复算。
_enum_bl = bl["inline_enum_pct"]
_med_e = float(_enum_bl.median())
_mad_e = float((_enum_bl - _med_e).abs().median())
rl("inline_enum_pct（含 '、' 的文本比例）: 2021 基线 %.3f%% | 2023 漂移池 %.3f%% | "
   "2018–2022 median %.3f%% / MAD %.3f%%（robust scale %.3f pp）"
   % (float(signals_of(base)["inline_enum_pct"]), float(signals_of(drift_pool)["inline_enum_pct"]),
      _med_e, _mad_e, 1.4826 * _mad_e))
rl("漂移池 %s ≥ 基线 %s ⇒ 100%% 剂量可无放回构造（理论上限 %.1f%%）"
   % (f"{len(drift_pool):,}", f"{len(base):,}", len(drift_pool) / len(base) * 100))

rows = []
rng0 = np.random.default_rng(SEED)
for dose in DOSES:
    m, n_drift = mixed_dose(dose)
    s = signals_of(m)
    diverge = float(np.mean((m["_A"] == 1) & (m["_B"] == 0)) * 1000)
    zs = {k_: robust_z(s[k_], float(bl[k_].median()), float((bl[k_] - bl[k_].median()).abs().median()))
          for k_ in SIGNALS}
    n_alarm = int(sum(abs(z) > 3 for z in zs.values()))
    rows.append({"dose_pct": dose, "n": len(m), "n_drift_2023": n_drift,
                 "naive_prev_pct": round(s["posrate_v3"], 2),
                 "explicit_prev_pct": round(float(np.mean(m["_B"])) * 100, 2),
                 "prev_distortion_pp": round(float(np.mean(m["_B"])) * 100 - s["posrate_v3"], 2),
                 "diverge_per_1000": round(diverge, 1),
                 "kappa_v1v3": round(s["kappa_v1v3"], 3),
                 "n_alarm_signals": n_alarm,
                 "alarm": bool(n_alarm >= 2),
                 "z_agreement": round(zs["agreement_pct"], 2),
                 "z_kappa": round(zs["kappa_v1v3"], 2),
                 "z_enum": round(zs["inline_enum_pct"], 2)})
    rl(f"dose={dose:2d}%  naive={s['posrate_v3']:.2f}%  分歧/1000={diverge:.1f}  "
       f"κ(v1×v3)={s['kappa_v1v3']:.3f}  报警信号数={n_alarm} → {'ALARM' if n_alarm >= 2 else 'no'}")

out = pd.DataFrame(rows)
os.makedirs(OUT, exist_ok=True)
out.to_csv(os.path.join(OUT, "wp1_drift_dose_response.csv"), index=False, encoding="utf-8-sig")
rl("\n注：① HR 畸变曲线未含（需逐剂量 Cox 重拟合，日间决策：全量 vs 子样本）；"
   "② ngram 位移信号未含（计算重，8/9 信号已覆盖一致性+风格族）；"
   "③ 剂量实验用真实 2023 记录为漂移材料（保真），非合成扰动。")
with open(os.path.join(OUT, "wp1_drift_dose_response_summary.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rep) + "\n")
rl("DONE")
