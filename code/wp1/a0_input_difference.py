# -*- coding: utf-8 -*-
"""a0_input_difference.py —— 数据切口 gate：baseline vs production freeze 分析层关键列逐行 diff

目的：判定 production freeze 值级置空补课（D-022）是否触及the study 下游分析（primary Cox model / baseline table）的输入列。
逻辑：对 (id, year) 对齐后，逐列比较 baseline 快照与 production freeze 现行 analysis_frame；
     文本派生结局（ecg_abnormal 等）与 primary 模型全部协变量逐位列出差异数。
结论规则：primary 模型输入列 diff 全 0 → 主分析数字可证明不变，备案"复核一致"；
        否则列出受影响行数与方向 → 决定是否全链重跑。
输出：results/a0_input_diff.csv（列级汇总）+ results/a0_input_diff_rows.csv（差异行明细，仅前 500 行）
"""
import os
import sys
import pandas as pd

STUDY_ROOT = r"study-data-root"
V35 = os.path.join(STUDY_ROOT, "data", "processed", "analysis_frame_baseline.csv")
V36 = os.path.join(STUDY_ROOT, "data", "processed", "analysis_frame.csv")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# primary 模型输入列（HARM/FULL 并集 + 基础三列）+ 文本派生结局 + masld 组件
COLS = ["age", "sex_male", "masld", "fat_state", "fatty",
        "sii_q", "proteinuria", "bmi", "htn_screen", "dm_screen",
        "tyg", "waist", "fpg", "egfr", "central_obese", "high_tg",
        "hyperuricemia", "ecg_abnormal"]

print("loading baseline ...", flush=True)
a = pd.read_csv(V35, encoding="utf-8-sig", dtype={"id": str}, low_memory=False)
print("loading production freeze ...", flush=True)
b = pd.read_csv(V36, encoding="utf-8-sig", dtype={"id": str}, low_memory=False)

print(f"baseline rows={len(a)}  production freeze rows={len(b)}", flush=True)
keys = ["id", "year"]
m = a.merge(b, on=keys, suffixes=("_v35", "_v36"), how="outer", indicator=True)
print("merge:", m["_merge"].value_counts().to_dict(), flush=True)
assert (m["_merge"] == "both").all(), "key sets differ!"

rows = []
for c in COLS:
    ca, cb = f"{c}_v35", f"{c}_v36"
    if ca not in m.columns or cb not in m.columns:
        rows.append({"column": c, "status": "MISSING", "n_diff": None,
                     "n_value_to_nan": None, "n_value_changed": None})
        continue
    va, vb = m[ca], m[cb]
    both_nan = va.isna() & vb.isna()
    diff = ~(va == vb) & ~both_nan
    to_nan = diff & vb.isna()
    chg = diff & ~vb.isna()
    rows.append({"column": c, "status": "OK",
                 "n_diff": int(diff.sum()),
                 "n_value_to_nan": int(to_nan.sum()),
                 "n_value_changed": int(chg.sum())})
    if diff.sum() > 0:
        ex = m.loc[diff, keys + [ca, cb]].head(500)
        ex.to_csv(os.path.join(OUT, "a0_input_diff_rows.csv"), index=False, encoding="utf-8-sig")

summ = pd.DataFrame(rows)
summ.to_csv(os.path.join(OUT, "a0_input_diff.csv"), index=False, encoding="utf-8-sig")
print(summ.to_string(index=False), flush=True)

version_contrast_cols = [r for r in rows if r["column"] in
            ["age", "sex_male", "masld", "sii_q", "proteinuria", "bmi", "htn_screen",
             "dm_screen", "tyg", "waist", "fpg", "egfr", "central_obese", "high_tg",
             "hyperuricemia"]]
total_version_contrast_diff = sum(r["n_diff"] or 0 for r in version_contrast_cols)
print(f"\n=== A0 结论：primary 模型输入列差异总数 = {total_version_contrast_diff} ===", flush=True)
print("VERDICT:", "NO_RERUN_NEEDED（复核一致）" if total_version_contrast_diff == 0 else "RERUN_REQUIRED（需全链重跑）", flush=True)
