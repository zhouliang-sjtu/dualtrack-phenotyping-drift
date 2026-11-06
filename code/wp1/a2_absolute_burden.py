# -*- coding: utf-8 -*-
"""a2_absolute_burden.py —— 绝对误分类负担（分层加权，遵守导师 §8 警示）

设计（禁止 85%×全体简单外推）：
  分歧核（2023）= naive(A)=1 & explicit(B)=0，结构 = 规则层 2,828（纯节律→normal，按构建）
                 + panel 池 376（左心室高电压/Q-T/早期复极等；376 = divergence core minus rule layer; the earlier working figure of 312 is superseded）。
  panel 池的误分类率由 S1 决策层（n=100，自池内 SRS）估计：15 异常 / 76 正常 / 9 不可判读
                 → 误分类（naive 判异常而 panel 判正常或不可判读）= 85/100。
  加权误分类 = 规则层 2,828 × 100% + 312 × (85/100)，CI 对 100 例决策层做非参数 bootstrap（B=10000）。
  逐年分歧核（naive vs explicit）从 S v3 flags 缓存（122,575 全库）精确复算——
  裁定规则是确定性聚合，其修正幅度即逐年分歧核规模；人体实测效度 = 160-record adjudication data set结果（2023）。

来源：160-record adjudication analysis report（panel 定稿：S1 15/76/9；κ=0.985）；层结构说明。
输出：results/wp1_definition_divergence_peryear.csv
     results/wp1_absolute_burden_2023.csv
     results/wp1_absolute_burden_summary.txt
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = r"STUDY_ROOT"
STUDY_ROOT = r"study-data-root"
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "results")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

rep = []


def rl(s=""):
    print(s, flush=True)
    rep.append(str(s))


rl("=== absolute misclassification burden（分层加权）===")

# ---------- 1) 全库逐年分歧核（主分析缓存口径，与主分析同序） ----------
d = pd.read_csv(os.path.join(STUDY_ROOT, "data", "processed", "analysis_frame.csv"),
                encoding="utf-8-sig", dtype={"id": str, "ecg_text": str}, low_memory=False)
d = d.sort_values(["id", "year"]).reset_index(drop=True)
c = pd.read_csv(os.path.join(RES, "v3_flags_cache.csv.gz"), encoding="utf-8-sig")
assert len(c) == len(d), f"缓存行数 {len(c)} ≠ 帧行数 {len(d)}"
for col in c.columns:
    d[col] = c[col].to_numpy()

ENUM = ["v3_ecg_af", "v3_ecg_pac_pvc", "v3_ecg_stt", "v3_ecg_rate", "v3_ecg_srirr",
        "v3_ecg_axis", "v3_ecg_qwave_mi", "v3_ecg_avblock", "v3_ecg_bbb"]
has_text = d["ecg_text"].notna()
A = np.where((pd.to_numeric(d["v3_ecg_normal"], errors="coerce") == 0) &
             (pd.to_numeric(d["v3_ecg_unreadable"], errors="coerce") == 0), 1.0, 0.0)
A[~has_text.to_numpy()] = np.nan
Bx = ((d[ENUM].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1) > 0) |
      (pd.to_numeric(d["v3_ecg_avblock"], errors="coerce").fillna(0) +
       pd.to_numeric(d["v3_ecg_bbb"], errors="coerce").fillna(0) > 0)).astype(float)
Bx[~has_text.to_numpy()] = np.nan
d["_A"], d["_B"] = A, Bx
d["_unr"] = pd.to_numeric(d["v3_ecg_unreadable"], errors="coerce").fillna(0)

rows = []
for y, g in d[has_text].groupby("year"):
    y = int(y)
    n = len(g)
    a = g["_A"]
    b = g["_B"]
    div_ab = int(((a == 1) & (b == 0) & (g["_unr"] == 0)).sum())
    div_ba = int(((a == 0) & (b == 1)).sum())
    rows.append({"year": y, "n_texts": n,
                 "naive_abn_n": int(a.sum()), "naive_abn_pct": round(a.mean() * 100, 2),
                 "explicit_abn_n": int(b.sum()), "explicit_abn_pct": round(b.mean() * 100, 2),
                 "prevalence_shift_pp": round((b.mean() - a.mean()) * 100, 2),
                 "diverge_A1B0": div_ab, "diverge_A0B1": div_ba,
                 "diverge_per_1000": round(div_ab / n * 1000, 1)})
pery = pd.DataFrame(rows)
rl(pery.to_string(index=False))

# ---------- 2) 2023 分层加权误分类（160-record adjudication data set实测 + 预注册规则层） ----------
y23 = pery[pery["year"] == 2023].iloc[0]
n_core = int(y23["diverge_A1B0"])          # 2023 分歧核（A=1,B=0,非unreadable）
rl(f"\n2023 分歧核（naive 阳性 & enumerated 阴性，非 unreadable）复算 = {n_core}（与 definition_alignment_notes.txt 口径逐位一致："
   f"3,204/21,661=14.8%; the earlier working figures 3,140/312 are superseded)")
RULE_LAYER = 2828
POOL = n_core - RULE_LAYER
assert 250 <= POOL <= 450, f"panel 池规模异常：{POOL}"
rl(f"对账（2026-09-21 夜）：规则层留痕文件 2,828 id ⊆ 分歧核 3,204（0 例外）→ panel 池 = {POOL}；"
   f"规则 = 生产词典 rhythm-only（_rule_layer_rhythm_normal_2023.csv is_rhythm 列）")
# 口径 A（分母 A）：2023 全部人年记录 = 21,661。
#   溯源：results/audit_number_baseline.txt L1（"21661 # 2023 全部人年记录总数"，
#   definition_alignment_notes.txt L29：3,204/21,661 = 14.8%）；
#   实测复核：review 阶段证据目录下的 probe_f6_denom2023.py
#   → analysis_frame.csv 2023 帧行数 MATCH（2026-11-01，结果已落盘）。
#   仅 misclassified_per_1000_* 两行使用本分母（145.3 / [143.9, 146.3]）；
#   逐表 prevalence 与 per_1000（148.2）走口径 B = y23["n_texts"] = 21,625（ecg_text 非空），
#   A − B = 36 条，全额为 ecg_text 缺失或空白，非去重亦非质控剔除。
#   注意：per-1,000 的分母必须是 DENOM_2023（口径 A），不得用 y23["n_texts"]（口径 B）——
#   后者会得 145.6 (144.1-146.5) 而非 145.3 (143.9-146.3)。
DENOM_2023 = 21661

# S1 决策层（n=100，自池 SRS）：15 异常 / 76 正常 / 9 不可判读（160-record adjudication analysis report §五，panel 定稿）
DEC_N, DEC_ABN, DEC_NORM, DEC_UNR = 100, 15, 76, 9
mis_rate_s1 = (DEC_NORM + DEC_UNR) / DEC_N          # naive 判异常而实为 正常/不可判读
# 决策层比例的 95%CI：Wilson 区间（与项目 tableS5_wilson_gates 口径一致），作用于池加权
z = 1.959963985
p_hat = mis_rate_s1
wd = 1 + z * z / DEC_N
wc = (p_hat + z * z / (2 * DEC_N)) / wd
wh = z * np.sqrt(p_hat * (1 - p_hat) / DEC_N + z * z / (4 * DEC_N * DEC_N)) / wd
mis_pool = POOL * p_hat
lo = POOL * max(0.0, wc - wh)
hi = POOL * min(1.0, wc + wh)
total_mis = RULE_LAYER + mis_pool
lo_t, hi_t = RULE_LAYER + lo, RULE_LAYER + hi

burden = pd.DataFrame([
    {"item": "divergence_core_2023_A1B0_nonunreadable", "value": n_core, "unit": "records",
     "source": "S v3 flags 缓存全库复算（本脚本 §1）"},
    {"item": "rule_layer_rhythm_normal", "value": RULE_LAYER, "unit": "records",
     "source": "study analysis frame, section 5 (_rule_layer_rhythm_normal_2023.csv; prespecified rule: pure rhythm to normal, applied as built)"},
    {"item": "panel_pool_residual", "value": POOL, "unit": "records",
     "source": "divergence core minus rule layer (376; the earlier working figure of 312 is superseded)"},
    {"item": "s1_decision_sample_n", "value": DEC_N, "unit": "records",
     "source": "160-record adjudication data set S1 决策层（自 panel 池 SRS）"},
    {"item": "s1_panel_result", "value": f"{DEC_ABN} 异常 / {DEC_NORM} 正常 / {DEC_UNR} 不可判读",
     "unit": "-", "source": "160-record adjudication analysis report §五（panel 定稿，κ=0.985）"},
    {"item": "pool_misclassification_est", "value": round(mis_pool, 1), "unit": "records",
     "source": f"{POOL} × {mis_rate_s1:.2f}（SRS 简单加权）"},
    {"item": "pool_misclassification_CI", "value": f"[{lo:.1f}, {hi:.1f}]", "unit": "records",
     "source": "决策层 100 例 Wilson 95% CI 作用于池加权（tableS5_wilson_gates 同口径）"},
    {"item": "total_misclassification_2023", "value": round(total_mis, 1), "unit": "records",
     "source": "规则层（按构建）+ 池加权估计"},
    {"item": "total_misclassification_2023_CI", "value": f"[{lo_t:.1f}, {hi_t:.1f}]", "unit": "records",
     "source": "同上合并"},
    {"item": "misclassified_per_1000_reports_2023", "value": round(total_mis / DENOM_2023 * 1000, 1),
     "unit": "per 1000", "source": f"total / {DENOM_2023}（authoritative denominator）× 1000"},
    {"item": "misclassified_per_1000_CI", "value": f"[{lo_t / DENOM_2023 * 1000:.1f}, {hi_t / DENOM_2023 * 1000:.1f}]",
     "unit": "per 1000", "source": "同上"},
    {"item": "false_abnormal_share", "value": "100%", "unit": "-",
     "source": "分歧核全部为 naive 判异常、裁定后 正常/不可判读（false abnormal 方向）"},
])
rl("\n" + burden.to_string(index=False))

os.makedirs(OUT, exist_ok=True)
pery.to_csv(os.path.join(OUT, "wp1_definition_divergence_peryear.csv"), index=False, encoding="utf-8-sig")
burden.to_csv(os.path.join(OUT, "wp1_absolute_burden_2023.csv"), index=False, encoding="utf-8-sig")
with open(os.path.join(OUT, "wp1_absolute_burden_summary.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rep) + "\n")
rl("\nDONE")
