# -*- coding: utf-8 -*-
"""a3_primary_analysis_lock.py —— primary analysis 唯一化（production freeze 审计）

依据：results/audit_number_check.csv（2026-09-20 23:48，production freeze 产物全量数字审计 ALL PASS）
     + results/version_contrast_summary.txt（production freeze 全套：TOST 双通过、LRT P=0.000245）。
主分析锁定：adjudicated（V3.0 显式阳性）定义 + year FE 为唯一 primary；
naive 与 definition grid 全谱降 secondary；ST–T = falsification control。

输出：results/wp1_primary_analysis_lock.csv + wp1_primary_analysis_summary.txt
"""
import os
import sys

import pandas as pd

ROOT = r"STUDY_ROOT"
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "results")

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

aud = pd.read_csv(os.path.join(RES, "audit_number_check.csv"), encoding="utf-8-sig")
assert (aud["verdict"] == "PASS").all(), "审计存在非 PASS 项，禁锁！"


def claim(aid):
    return aud.loc[aud["id"].astype(str) == aid, ["claim", "claimed", "actual"]].iloc[0]


rows = []
for aid, role, spec, note in [
    ("P15", "PRIMARY", "adjudicated (V3.0 explicit) production, no FE", "manuscript 口径；production freeze 审计 PASS"),
    ("P10", "PRIMARY-FE", "v3 + year FE (harmonized spec)", "0.964 (0.9236–1.0061)，n=46,973"),
    ("P14", "SECONDARY", "naive production + year FE", "0.961 p=0.054"),
    ("P13", "SECONDARY", "naive production, no FE", "0.959 p=0.043"),
    ("P16", "SECONDARY", "spec-curve median (24 specs)", "0.969"),
    ("P17", "SECONDARY", "version ΔHR (yearFE)", "+0.0018，TOST ±5% 双通过（production freeze）"),
    ("P2", "FALSIFICATION-CONTROL", "ST-T fullcov", "1.078 p=0.0077（template-insensitive 内部阳性对照）"),
    ("P3", "FALSIFICATION-CONTROL", "ST-T +FE", "1.074 p=0.0067"),
]:
    c = claim(aid)
    rows.append({"role": role, "spec": spec, "claim": c["claim"],
                 "claimed": c["claimed"], "actual_frozen": c["actual"], "audit": "PASS", "note": note})

lock = pd.DataFrame(rows)
os.makedirs(OUT, exist_ok=True)
lock.to_csv(os.path.join(OUT, "wp1_primary_analysis_lock.csv"), index=False, encoding="utf-8-sig")

txt = [
    "=== primary analysis lock（production freeze 审计）===",
    "PRIMARY = adjudicated (V3.0 explicit) + year FE 叙事；全部数字经 09-20 production freeze 审计 PASS。",
    "naive 与 24-spec grid 全部降 secondary；ST–T 为 falsification control。",
    "manuscript 规则：摘要只出现 PRIMARY 与 falsification control；P 值退居文字，不按 0.05 着色。",
    "",
    lock.to_string(index=False),
]
with open(os.path.join(OUT, "wp1_primary_analysis_summary.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(txt) + "\n")
print("\n".join(txt))
print("DONE")
