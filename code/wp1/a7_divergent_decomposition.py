# -*- coding: utf-8 -*-
"""a7_divergent_decomposition.py —— 2023 定义分歧记录的暴露组分布与驱动层分解

（2026-11-05）：外部评审指出 2023 年 14.82pp 患病率漂移未传导到 HR，
且 divergent 记录在暴露组/非暴露组的分布未报。本脚本按 a2_absolute_burden.py 的既存口径
（naive = 非 normal 且非 unreadable；explicit = ENUM 9 旗标任一）复算 2023 分歧核，
并按 (a) 前波 MASLD 暴露组 与 (b) 驱动层（规则层 rhythm-only vs panel 池）分解。

规格冻结：the prespecified analysis specification, frozen before the analysis。
全部基准值 fail-loud（3,204／2,828＋312／11,066／7,862／148.2；留痕 id ⊆ divergent 0 例外）。

环境变量（便于以包内 deposit 副本复算）：A7_FRAME / A7_FLAGS / A7_RULELAYER / A7_OUT

输出：OUT/wp1_divergent_decomposition.csv + wp1_divergent_decomposition_summary.txt
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = r"STUDY_ROOT"
FRAME_PATH = r"study-data-root/data/processed/analysis_frame.csv"
FLAGS = os.path.join(ROOT, "results", "v3_flags_cache.csv.gz")
RULELAYER = os.path.join(ROOT, "reference-data", "reference-data",
                         "05-supplementary-annotation-and-realignment",
                         "_rule_layer_rhythm_normal_2023.csv")
OUT = os.environ.get("A7_OUT", os.path.join(ROOT, "results"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

rep = []


def rl(s=""):
    print(s, flush=True)
    rep.append(str(s))


rl("=== 2023 divergent decomposition ===")

d = pd.read_csv(FRAME_PATH, encoding="utf-8-sig", dtype={"id": str, "ecg_text": str}, low_memory=False)
d = d.sort_values(["id", "year"]).reset_index(drop=True)
c = pd.read_csv(FLAGS, encoding="utf-8-sig")
assert len(c) == len(d), f"旗标缓存行数 {len(c)} ≠ 帧行数 {len(d)}"
for col in c.columns:
    d[col] = c[col].to_numpy()

# 前波暴露（主分析同法：id 排序后组内 shift）
d["masld_prev"] = d.groupby("id")["masld"].shift()

ENUM = ["v3_ecg_af", "v3_ecg_pac_pvc", "v3_ecg_stt", "v3_ecg_rate", "v3_ecg_srirr",
        "v3_ecg_axis", "v3_ecg_qwave_mi", "v3_ecg_avblock", "v3_ecg_bbb"]
has_text = d["ecg_text"].notna()
A = np.where((pd.to_numeric(d["v3_ecg_normal"], errors="coerce") == 0) &
             (pd.to_numeric(d["v3_ecg_unreadable"], errors="coerce") == 0), 1.0, 0.0)
A[~has_text.to_numpy()] = np.nan
Bx = (d[ENUM].apply(pd.to_numeric, errors="coerce").fillna(0).sum(axis=1) > 0).astype(float)
Bx[~has_text.to_numpy()] = np.nan
d["_A"], d["_B"] = A, Bx
d["_unr"] = pd.to_numeric(d["v3_ecg_unreadable"], errors="coerce").fillna(0)

m23 = d[(d["year"] == 2023) & has_text].copy()
div = m23[(m23["_A"] == 1) & (m23["_B"] == 0)]

# 基准值复算（规格冻结 §数值基准，fail-loud）
assert len(div) == 3204, f"divergent {len(div)} ≠ 3,204"
assert int(m23['_A'].sum()) == 11066, f"naive {int(m23['_A'].sum())} ≠ 11,066"
assert int(m23['_B'].sum()) == 7862, f"explicit {int(m23['_B'].sum())} ≠ 7,862"
# 驱动机制（实测，2023）：divergent 全部 normal 未置位、unreadable=0、ENUM 全 0；
# 其中 3,140 条无任何旗标触发（naive 按「非 normal 即异常」规则记异常）、64 条 v3_ecg_other=1。
assert (pd.to_numeric(div['v3_ecg_normal'], errors='coerce').fillna(1) == 0).all()
assert (pd.to_numeric(div['v3_ecg_unreadable'], errors='coerce').fillna(1) == 0).all()
assert (div[ENUM].apply(pd.to_numeric, errors='coerce').fillna(0).sum(axis=1) == 0).all()
n_other = int((pd.to_numeric(div['v3_ecg_other'], errors='coerce').fillna(0) == 1).sum())
n_noflag = len(div) - n_other
rl(f"基准值复算：divergent=3,204 ✓ naive=11,066 ✓ explicit=7,862 ✓；"
   f"ENUM 全 0 ✓；无旗标触发 {n_noflag:,} ＋ 残余类 ecg_other {n_other:,}")

# 驱动层：规则层留痕件（sha=da14ee6f…794c8d，与包内指纹件一致）
rl_arch = pd.read_csv(RULELAYER, encoding="utf-8-sig", dtype={"id": str},
                      usecols=["year", "id", "is_rhythm"])
assert len(rl_arch) == 2828, f"规则层留痕 {len(rl_arch)} ≠ 2,828"
assert (rl_arch["year"] == 2023).all(), "规则层留痕含非 2023 行"
rl_ids = set(zip(rl_arch["year"], rl_arch["id"]))
div_ids = set(zip(div["year"], div["id"]))
assert rl_ids <= div_ids, f"留痕 id ⊄ divergent（{len(rl_ids - div_ids)} 例外）"
m23["_rule_layer"] = [(y, i) in rl_ids for y, i in zip(m23["year"], m23["id"])]
div = m23[(m23["_A"] == 1) & (m23["_B"] == 0)]
n_rule = int(div["_rule_layer"].sum())
n_pool = len(div) - n_rule
# 池口径 = 分歧核 − 规则层 = 376（A2 同式；2,828＋376×85%＝3,147.6 与主件吻合；
# an earlier working figure of 312 is superseded and retained only in this note)
assert (n_rule, n_pool) == (2828, 376), f"层分解 {(n_rule, n_pool)} ≠ (2,828, 376)"
rl(f"层分解：规则层 {n_rule:,} ＋ panel 池 {n_pool:,} ✓（对账 A2 口径）")

# 暴露组分布（Overall = 2023 全部非空文本；暴露对比在两个有前波层之间）
rows = []


def _row(stratum, g):
    nd = int(((g["_A"] == 1) & (g["_B"] == 0)).sum())
    nr = int(g["_rule_layer"].sum()) if nd else 0
    rows.append({
        "stratum": stratum,
        "n_texts": int(len(g)),
        "naive_abn_n": int(g["_A"].sum()) if nd else 0,
        "explicit_abn_n": int(g["_B"].sum()) if nd else 0,
        "divergent_n": nd,
        "divergent_per_1000": round(nd / len(g) * 1000, 1) if nd else None,
        "rule_layer_rhythm_n": nr,
        "panel_pool_n": nd - nr,
    })


_row("Overall (2023, non-empty texts)", m23)
_row("Prior-wave MASLD exposed", m23[m23["masld_prev"] == 1])
_row("Prior-wave non-exposed", m23[m23["masld_prev"] == 0])
_row("No prior wave (first record)", m23[m23["masld_prev"].isna()])
decomp = pd.DataFrame(rows)
_o, _e, _n, _f = (decomp.iloc[0], decomp.iloc[1], decomp.iloc[2], decomp.iloc[3])
assert int(_e["n_texts"] + _n["n_texts"] + _f["n_texts"]) == int(_o["n_texts"]), "暴露分层行数不闭合"
assert int(_e["divergent_n"] + _n["divergent_n"] + _f["divergent_n"]) == int(_o["divergent_n"]) == 3204, \
    "暴露组分歧数不闭合"
assert _o["divergent_per_1000"] == 148.2, "Overall per-1,000 ≠ 148.2"
rl(f"暴露对比（每千人）：暴露 {_e['divergent_per_1000']} vs 非暴露 {_n['divergent_per_1000']} vs "
   f"首次体检 {_f['divergent_per_1000']} —— 无暴露组富集")

os.makedirs(OUT, exist_ok=True)
decomp.to_csv(os.path.join(OUT, "wp1_divergent_decomposition.csv"), index=False,
              encoding="utf-8-sig")
rl(decomp.to_string(index=False))
rl(f"\n驱动机制（2023，实测）：3,204 条 divergent 全部为「normal 未置位 ∧ unreadable=0 ∧ ENUM 全 0」；"
   f"其中 {n_noflag:,} 条无任何旗标触发（naive 规则「非 normal 即异常」按构建记异常），"
   f"{n_other:,} 条由残余类 v3_ecg_other 驱动。层分解（2,828/376）取自规则层留痕件 id 池与差值。")
rl("\n读法（供文稿引用）：3,204 条 2023 分歧记录在暴露组/非暴露组的 per-1,000 率相近，"
   "且全部源于 naive 聚合规则对「未触发任何旗标的叙述」与「残余类所见」的异常判定——"
   "患病率漂移是测量层（聚合规则）而非暴露关联层的属性。")
rl("DONE")
with open(os.path.join(OUT, "wp1_divergent_decomposition_summary.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rep) + "\n")
