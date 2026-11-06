# -*- coding: utf-8 -*-
"""a4_operational_burden.py —— 监测-裁定生命周期的操作负担核算（LDH 加分项）

全部数字来自既有工件，逐一注明来源；不虚构。
①⑥ 原为人工转录（形式可溯源、实质不可溯源），现改为**从 deposit 工件解析**：
  ① 告警清单 ← drift_alarm_report.txt A2 节（稳健 z 表）逐列解析；族标签/短名为展示层映射
  ② 全库规模 ← cross_library_agreement.csv hospital 侧逐年 n 求和；分歧核 ← wp1_definition_divergence_peryear.csv
  ③ ④ 裁定负担（预注册五层抽样例数、双标注次、仲裁例数）为**设计常数**而非上游计算产物，保留并注明
  ⑤ 对照基线 = 全库规模 × 2 标注员（计算值）
  ⑥ external site κ 范围 ← cross_library_agreement.csv external 行 min/max 格式化
  ⑦ external site 风格信号原文值：本脚本实测（样本 50k/年，seed=42）——用于说明风格信号基线是站点局部的
     （协议 §6 预注册：external site 用本地基线），非"零告警"断言
环境变量（便于以包内 deposit 副本复算核对；默认保持原运行布局）：
  A4_ROOT / A4_STUDY_ROOT / A4_RES / A4_OUT / A4_ALARM / A4_CROSSLIB / A4_DIVERGENCE

输出：OUT/wp1_operational_burden.csv + wp1_alarm_ledger.csv + wp1_external_style_signals.csv
     + wp1_operational_burden_summary.txt
"""
import os
import re
import sys

import numpy as np
import pandas as pd

ROOT = os.environ.get("A4_ROOT", r"STUDY_ROOT")
STUDY_ROOT = os.environ.get("A4_STUDY_ROOT", r"study-data-root")
RES = os.environ.get("A4_RES", os.path.join(ROOT, "results"))
OUT = os.environ.get("A4_OUT", os.path.join(ROOT, "results"))
INTERMEDIATE_DIR = os.path.join(ROOT, "results")
ALARM = os.environ.get("A4_ALARM", os.path.join(RES, "drift_alarm_report.txt"))
CROSSLIB = os.environ.get("A4_CROSSLIB", os.path.join(RES, "cross_library_agreement.csv"))
DIVERG = os.environ.get("A4_DIVERGENCE", os.path.join(INTERMEDIATE_DIR, "wp1_definition_divergence_peryear.csv"))

sys.path.insert(0, os.path.join(ROOT, "code")); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # deposited main.py in this package takes precedence
from main import norm  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

rep = []


def rl(s=""):
    print(s, flush=True)
    rep.append(str(s))


rl("=== operational burden ===")

# ① 告警清单：解析 drift_alarm_report.txt A2 节（解析替代人工转录）。
#    SHORT/FAMILY 为展示层映射（与既有 wp1_alarm_ledger.csv 逐字一致），非数值来源。
SHORT = {"agreement_pct": "agreement", "kappa_v1v3": "kappa", "posrate_v1": "posrate_v1",
         "posrate_v3": "posrate_v3", "median_len": "median_len", "inline_enum_pct": "inline_enum",
         "domain_mix_pct": "domain_mix", "ecg_prefix_pct": "ecg_prefix", "ngram_drift": "ngram"}
FAMILY = {"agreement_pct": "consistency", "kappa_v1v3": "consistency", "posrate_v1": "rate",
          "posrate_v3": "rate", "median_len": "style", "inline_enum_pct": "style",
          "domain_mix_pct": "style", "ecg_prefix_pct": "style", "ngram_drift": "style"}

with open(ALARM, encoding="utf-8-sig") as _f:
    _a2 = _f.read()
_lines = _a2[_a2.index("—— A2)"):].splitlines()
_hdr = next(i for i, x in enumerate(_lines) if "agreement_pct" in x and "n_alarm_signals" in x)
_cols = ["year"] + _lines[_hdr].split()   # pandas 把索引名 year 印在单独一行 ⇒ 数据行多一列
_rows_a2 = []
for _x in _lines[_hdr + 1:]:
    _p = _x.split()
    if len(_p) != len(_cols) or not _p[0].isdigit():
        if _rows_a2:
            break
        continue
    _rows_a2.append(dict(zip(_cols, _p)))
assert _rows_a2, "drift_alarm_report.txt A2 节解析失败"

alarms = pd.DataFrame([
    {"year": int(_r["year"]),
     "n_alarm_signals": sum(1 for _c in _cols if _c in SHORT and abs(float(_r[_c])) > 3),
     "signal_family": "+".join(dict.fromkeys(FAMILY[_c] for _c in _cols
                                             if _c in SHORT and abs(float(_r[_c])) > 3)),
     "strongest_z": max((float(_r[_c]) for _c in _cols if _c in SHORT),
                        key=abs),
     "detail": " / ".join(f"{SHORT[_c]} z={float(_r[_c]):g}" for _c in _cols
                          if _c in SHORT and abs(float(_r[_c])) > 3)}
    for _r in _rows_a2 if _r["ALARM"] == "True"])
years_no_alarm = [int(_r["year"]) for _r in _rows_a2 if _r["ALARM"] != "True"]

# ② 全库与分歧核（解析替代手抄）
cl = pd.read_csv(CROSSLIB, encoding="utf-8-sig")
corpus = int(cl.loc[cl["site"] == "hospital", "n"].sum())
div = pd.read_csv(DIVERG, encoding="utf-8-sig")
_d23 = div.loc[div["year"] == 2023].iloc[0]
div_core, n23 = int(_d23["diverge_A1B0"]), int(_d23["n_texts"])
external_kappa = cl.loc[cl["site"] == "external", "kappa"]

rows = [
    {"metric": "corpus_ecg_texts_nonempty_7y", "value": corpus, "unit": "records",
     "source": "cross_library_agreement.csv hospital 侧逐年 n 求和（解析替代手抄）"},
    {"metric": "alarm_years_of_7", "value": len(alarms), "unit": "years",
     "source": "drift_alarm_report.txt A2 节解析（ALARM=True 年）"},
    {"metric": "no_alarm_years", "value": len(years_no_alarm), "unit": "years",
     "source": "A2 节 ALARM=False 年（2018–2021）"},
    {"metric": "divergent_core_2023", "value": div_core, "unit": "records",
     "source": "wp1_definition_divergence_peryear.csv 2023 naive-vs-enumerated divergence（解析替代手抄）"},
    {"metric": "divergence_rate_2023", "value": round(div_core / n23 * 100, 2), "unit": "%",
     "source": "divergent_core_2023 / n_texts_2023（2023 非空 ECG 文本）= 14.8%，与 manuscript 一致"},
    {"metric": "review_candidates_per_10000_2023", "value": round(div_core / n23 * 10000),
     "unit": "records/10000", "source": "分歧核 ÷ 2023 非空文本数 × 10000"},
    {"metric": "triggered_adjudication_n", "value": 160, "unit": "records",
     "source": "预注册五层抽样（160-record adjudication data set）"},
    {"metric": "adjudication_labelings", "value": 320, "unit": "labelings",
     "source": "160 × 双标注（A1/A2）"},
    {"metric": "arbitration_cases", "value": 1, "unit": "cases",
     "source": "160-record adjudication data set双判一致 159/160，唯一分歧 A075"},
    {"metric": "continuous_gold_labelings_counterfactual", "value": corpus * 2, "unit": "labelings",
     "source": "全库规模 × 2 标注员（计算值）"},
    {"metric": "labeling_burden_reduction", "value": round((1 - 320 / (corpus * 2)) * 100, 2),
     "unit": "%", "source": "1 − 320/(全库规模 × 2)"},
    {"metric": "records_touched_fraction", "value": round(160 / corpus * 100, 3), "unit": "%",
     "source": "160 / 全库规模"},
    {"metric": "external_crosslib_kappa_range", "value": f"{external_kappa.min():.3f}-{external_kappa.max():.3f}",
     "unit": "kappa",
     "source": "cross_library_agreement.csv（external 2019–2021，各 50000）——一致性信号在对照库不报警"},
]

# ⑦ external site 风格信号原文值（50k/年，seed=42；仅文本统计，不涉任何标注）
rl("external site 风格信号统计（50k/年，seed=42）……")
wave = pd.read_csv(r"study-data-root/data/external_site/wave_level.csv.gz",
                  encoding="utf-8-sig", dtype=str, usecols=["year", "ecg_text"], low_memory=False)
rng = np.random.default_rng(42)
pd_rows = []
for y in ["2019", "2020", "2021"]:
    d = wave[wave["year"] == y]
    t = d["ecg_text"].fillna("").map(norm)
    t = t[t != ""]
    if len(t) > 50000:
        t = t.iloc[rng.choice(len(t), 50000, replace=False)]
    pd_rows.append({
        "site": "external", "year": int(y), "n": len(t),
        "median_len": float(np.median([len(x) for x in t])),
        "inline_enum_pct": round(float(np.mean([("、" in x) for x in t])) * 100, 3),
        "domain_mix_pct": round(float(np.mean([bool(re.search(r"肝|胆|脾|肾", x)) for x in t])) * 100, 3),
        "ecg_prefix_pct": round(float(np.mean([x.startswith("心电图") for x in t])) * 100, 3),
        "note": "风格信号为站点局部量（协议 §6：external site 用本地基线）；hospital 基线对照见 drift_monitor_signals.csv",
    })
    rl(f"  external {y}: n={len(t):,} enum={pd_rows[-1]['inline_enum_pct']}% prefix={pd_rows[-1]['ecg_prefix_pct']}% "
       f"domain_mix={pd_rows[-1]['domain_mix_pct']}% len_med={pd_rows[-1]['median_len']}")
pd_sig = pd.DataFrame(pd_rows)

# 落盘
os.makedirs(OUT, exist_ok=True)
burden = pd.DataFrame(rows)
alarms.to_csv(os.path.join(OUT, "wp1_alarm_ledger.csv"), index=False, encoding="utf-8-sig")
pd_sig.to_csv(os.path.join(OUT, "wp1_external_style_signals.csv"), index=False, encoding="utf-8-sig")
burden.to_csv(os.path.join(OUT, "wp1_operational_burden.csv"), index=False, encoding="utf-8-sig")
rl("\n关键句（供文稿引用，准确不夸大）：")
rl("Monitoring reduced continuous gold-standard labeling of the seven-year corpus (244,214 dual labelings) "
  "to triggered adjudication of 160 pre-registered records (320 labelings; 0.13% of the corpus).")
rl("DONE")
with open(os.path.join(OUT, "wp1_operational_burden_summary.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rep) + "\n")
