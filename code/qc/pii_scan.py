# -*- coding: utf-8 -*-
"""pii_scan.py —— 金标准文本 PII 扫描（伦理豁免申请与开源前必备检查，2026-09-02）
扫描对象：4个母体 gold_*.csv + 4个release to annotators版 dataset/*_to_annotate.csv 的 text 列（id/pseudo_id 列除外）
模式分级：
  高置信（0容忍）：手机号、身份证(18/15位)、座机、邮箱
  中置信（人工复核）：住址关键词、姓名+称谓组合
  低置信（统计参考）：连续≥7位数字（病历号/卡号/长编号）
输出: results/pii_scan_summary.csv, results/pii_scan_hits.csv
用法: python code/pii_scan.py
"""
import os
import re

import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # repository root
RES = os.path.join(BASE, "results")
os.makedirs(RES, exist_ok=True)

PATTERNS = [
    ("HIGH", "mobile", r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    ("HIGH", "idcard18", r"(?<!\d)\d{17}[\dXx](?!\d)"),
    ("HIGH", "idcard15", r"(?<!\d)\d{15}(?!\d)"),
    ("HIGH", "landline", r"(?<!\d)\d{3,4}-\d{7,8}(?!\d)"),
    ("HIGH", "email", r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    ("MID", "address", r"[\u4e00-\u9fa5]{2,12}?(?:省|市|区|县|路|街|巷|道|弄)\s*\d{0,4}号"),
    ("MID", "hometown", r"[\u4e00-\u9fa5]{2,8}(?:小区|花园|公寓|苑|庭)\s*\d{0,4}(?:栋|幢|号楼|单元|室)"),
    ("MID", "name_title", r"[\u4e00-\u9fa5]{1,2}(?:同志|女士|先生|老师|医师)"),
    ("MID", "name_field", r"(?:姓名|患者名|联系人)\s*[:：]\s*\S{1,12}"),
    ("LOW", "longnum", r"(?<!\d)\d{7,}(?!\d)"),
]

FILES = [
    ("mother", "data/reference_standard/ecg_full.csv", "text"),
    ("mother", "data/reference_standard/echo_full.csv", "text"),
    ("mother", "data/abdominal_ultrasound_primary.csv", "text"),
    ("mother", "data/reference_standard/abdomen_hospital_full.csv", "text"),
    ("release", "data/reference-data_dataset_ECG.csv", "text"),
]

# release 版实际路径
DS = os.path.join(BASE, "reference-data", "dataset")
FILES = [(src, os.path.join(BASE, p), col) for src, p, col in FILES]
RELEASE = [
    ("release", os.path.join(DS, "ECG_to_annotate.csv")),
    ("release", os.path.join(DS, "ECHOCARDIOGRAPHY_to_annotate.csv")),
    ("release", os.path.join(DS, "ABDOMINAL_ULTRASOUND_PRIMARY_to_annotate.csv")),
    ("release", os.path.join(DS, "ABDOMINAL_ULTRASOUND_HOSPITAL_to_annotate.csv")),
]
FILES = FILES[:4] + [(s, p, "text") for s, p in RELEASE]

summary, hits = [], []
for src, path, col in FILES:
    fname = os.path.basename(path)
    if not os.path.exists(path):
        print(f"[缺文件] {path}")
        continue
    d = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    rows = len(d)
    counts = {p[1]: 0 for p in PATTERNS}
    for _, r in d.iterrows():
        text = str(r.get(col, ""))
        sid = str(r.get("sample_id", r.name))
        for level, name, pat in PATTERNS:
            for m in re.finditer(pat, text):
                counts[name] += 1
                s, e = max(0, m.start() - 20), min(len(text), m.end() + 20)
                hits.append({"source": src, "file": fname, "sample_id": sid,
                             "level": level, "pattern": name, "match": m.group()[:40],
                             "context": text[s:e].replace("\n", " ")})
    summary.append({"source": src, "file": fname, "rows": rows, **counts})

# ================= 全量数据集扫描（平台治理条款坐实） =================
FULL_FILES = [
    ("full_hospital", os.environ.get("HOSPITAL_CHECKUP_LONG", ""), ["id", "ecg_text"]),
    ("full_hospital_analysis", os.environ.get("HOSPITAL_ANALYSIS_LONG", ""), ["id", "ecg_text"]),
    ("full_hospital_us", os.environ.get("HOSPITAL_US_TEXT", ""), ["id", "us_text", "main_text"]),
    ("full_primary", os.environ.get("EXTERNAL_ARM_LONG", ""), None),  # None=全部文本列自动识别
]
for src, path, cols in FULL_FILES:
    fname = os.path.basename(path)
    if not os.path.exists(path):
        print(f"[缺文件·全量] {path}")
        continue
    if cols is None:
        head = pd.read_csv(path, encoding="utf-8-sig", nrows=5, dtype=str)
        cols = [c for c in head.columns if "text" in c.lower()]
    d = pd.read_csv(path, encoding="utf-8-sig", usecols=cols, dtype=str)
    rows = len(d)
    counts = {p[1]: 0 for p in PATTERNS}
    for _, r in d.iterrows():
        sid = str(r.get("id", r.name))
        for col in cols:
            if col == "id":
                continue  # id 列为原始标识字段，属本地驻场层，不在发布范围；另行管理
            text = str(r.get(col, ""))
            if text == "nan" or not text.strip():
                continue
            for level, name, pat in PATTERNS:
                for m in re.finditer(pat, text):
                    counts[name] += 1
                    s, e = max(0, m.start() - 20), min(len(text), m.end() + 20)
                    hits.append({"source": src, "file": fname, "sample_id": sid,
                                 "level": level, "pattern": name, "match": m.group()[:40],
                                 "context": text[s:e].replace("\n", " ")})
    summary.append({"source": src, "file": fname + f" ({','.join(c for c in cols if c != 'id')})", "rows": rows, **counts})
    print(f"[全量] {fname}: {rows} 行扫描完成，当前累计命中 {sum(v for v in counts.values())}")

sm = pd.DataFrame(summary)
sm.to_csv(os.path.join(RES, "pii_scan_summary.csv"), index=False, encoding="utf-8-sig")
hd = pd.DataFrame(hits)
hd.to_csv(os.path.join(RES, "pii_scan_hits.csv"), index=False, encoding="utf-8-sig")
print("=== PII 扫描汇总（命中次数） ===")
print(sm.to_string(index=False))
hi = hd[hd["level"] == "HIGH"] if len(hd) else hd
print(f"\n高置信命中: {len(hi)} 条")
if len(hi):
    print(hi[["source", "file", "sample_id", "pattern", "match", "context"]].head(20).to_string(index=False))
print(f"\n明细 -> {RES}/pii_scan_hits.csv（全部命中含中低置信，供人工复核）")
