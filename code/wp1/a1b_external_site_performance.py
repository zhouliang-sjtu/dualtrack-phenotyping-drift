# -*- coding: utf-8 -*-
"""a1b_external_site_performance.py —— primary 外部站点（第二机构）表型级性能

定位：金标准四域中 ECHOCARDIOGRAPHY(300)/ABDOMINAL_ULTRASOUND_PRIMARY(300) 系 **primary 合作方体系**（与 hospital 不可链接的第二机构，
     快照 v2.1 §0）的盲法双标注+仲裁参照——这构成 ECHO/abdominal ultrasound 两域的"外部站点参照标准"。
     本脚本把冻结抽取器在这 600 份外部标注上的表型级性能正式产出（此前仅隐含于"四域金标准"中）。
     ECG 主域的外部标注缺口由 external site 400–600 例标注集补齐。

轨迹：
  ECHO  — 词典轨 extract_echo 重放（record 级复合结局可算）；LLM 轨 flag 级引用既有验收结果表
  abdominal ultrasound — 词典轨 extract_abd 重放（primary 文本=【检查所见】无主检，与函数设计一致）

金标准终值：三层解析（逐变量裁定 → 案级裁定 → rule-first 维持 A1，逐格留痕）。
输出：results/wp1_external_site_performance.csv（flag 级长表）
     results/wp1_external_site_composite.csv（复合结局）+ summary txt
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = r"STUDY_ROOT"
OUT = os.path.join(ROOT, "results")
GOLD = os.path.join(ROOT, "data", "gold_standard_annotation_workbook_final.xlsx")
SEED = 20260921
B = 1000

sys.path.insert(0, os.path.join(ROOT, "code")); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # deposited main.py in this package takes precedence
from main import extract_echo, extract_abd, norm  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

rep = []


def rl(s=""):
    print(s, flush=True)
    rep.append(str(s))


rl("=== 外部站点性能（ECHOCARDIOGRAPHY 300 / ABDOMINAL_ULTRASOUND_PRIMARY 300）===")
arb = pd.read_excel(GOLD, sheet_name="仲裁裁定_两轮", dtype=str)


def resolve_final(sheet, vars_, prefix):
    """三层终值解析，返回 (final_df, n_dis, rule_first_list)"""
    wb = pd.read_excel(GOLD, sheet_name=sheet, dtype=str)
    dom_arb = arb[arb["域"] == sheet]
    var_ruling = dom_arb[dom_arb["变量"].notna()].set_index(["变量", "sample_id"])["仲裁裁定"]
    case_ruling = dom_arb[dom_arb["变量"].isna()].set_index("sample_id")["仲裁裁定"]
    g = wb.copy()
    n_dis, rule_first, unresolved = 0, [], []
    for v in vars_:
        a1 = pd.to_numeric(g[prefix + v], errors="coerce")
        a2 = pd.to_numeric(g["A2_" + v], errors="coerce")
        n_dis += int((a1 != a2).sum())
        fin = a1.where(a1 == a2)
        for i in g.index[fin.isna() & a1.notna() & a2.notna()]:
            sid = g.at[i, "sample_id"]
            val = None
            if (v, sid) in var_ruling.index:
                val = pd.to_numeric(var_ruling.loc[(v, sid)], errors="coerce")
            elif sid in case_ruling.index:
                val = pd.to_numeric(case_ruling.loc[sid], errors="coerce")
            if val is None or pd.isna(val):  # 无裁定或"维持"类文本裁定 → L3 维持 A1 留痕
                fin.at[i] = a1.at[i]
                rule_first.append(f"{v}:{sid}")
            else:
                fin.at[i] = val
            if pd.isna(fin.at[i]):
                unresolved.append(f"{v}:{sid}")
        g["F_" + v] = fin
    if rule_first:
        print(f"  [{sheet}] L3 rule-first 维持A1（无案级裁定，逐格留痕）：{rule_first}")
    assert not unresolved, f"未决：{unresolved}"
    return g, n_dis, rule_first


def kappa(a, b):
    a, b = np.asarray(a), np.asarray(b)
    labs = sorted(set(a) | set(b))
    po = float(np.mean(a == b))
    pe = sum(float(np.mean(a == L)) * float(np.mean(b == L)) for L in labs)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def prf(y_t, y_p, pos=1):
    tp = int(((y_t == pos) & (y_p == pos)).sum())
    fp = int(((y_t != pos) & (y_p == pos)).sum())
    fn = int(((y_t == pos) & (y_p != pos)).sum())
    tn = int(((y_t != pos) & (y_p != pos)).sum())
    sens = tp / (tp + fn) if tp + fn else np.nan
    spec = tn / (tn + fp) if tn + fp else np.nan
    ppv = tp / (tp + fp) if tp + fp else np.nan
    npv = tn / (tn + fn) if tn + fn else np.nan
    f1 = (2 * ppv * sens / (ppv + sens)) if (sens == sens and ppv == ppv and (ppv + sens) > 0) else np.nan
    return sens, spec, ppv, npv, f1


def boot_ci(y_t, y_p, stat_fn, persons):
    uniq = pd.unique(persons)
    idx = {p: np.where(persons == p)[0] for p in uniq}
    rng = np.random.default_rng(SEED)
    vals = []
    for _ in range(B):
        ps = rng.choice(uniq, size=len(uniq), replace=True)
        bi = np.concatenate([idx[p] for p in ps])
        v = stat_fn(y_t[bi], y_p[bi])
        if v == v:
            vals.append(v)
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


flag_rows, comp_rows = [], []

# ================= ECHOCARDIOGRAPHY =================
ECHO_VARS = ["echo_normal", "echo_variant", "echo_lvh", "echo_la_dilate",
             "ef_abnormal", "echo_rhythm", "echo_unreadable"]
g, n_dis, rf = resolve_final("ECHOCARDIOGRAPHY", ECHO_VARS, "A1_")
rl(f"ECHOCARDIOGRAPHY：分歧格 {n_dis}，rule-first {len(rf)} {rf[:5]}")
replay = [extract_echo(norm(t)) for t in g["text"].fillna("")]
g["ext_label"] = [r["label"] for r in replay]
g["ext_lvh"] = [r["lvh"] for r in replay]
g["ext_la"] = [r["la_dilate"] for r in replay]
g["ext_ef"] = [r["ef"] for r in replay]
g["ext_reflux"] = [r["reflux_grade"] for r in replay]
g["ext_rhythm"] = [r["rhythm"] for r in replay]

persons = g["pseudo_id"].to_numpy()
# flag 级（二值变量）
for v, ext_series in [("echo_lvh", g["ext_lvh"]), ("echo_la_dilate", g["ext_la"]),
                      ("echo_rhythm", g["ext_rhythm"])]:
    y_t = g["F_" + v].astype(float).to_numpy()
    y_p = pd.to_numeric(ext_series, errors="coerce").fillna(0).to_numpy()
    k = kappa(y_t, y_p)
    lo, hi = boot_ci(y_t, y_p, kappa, persons)
    sens, spec, ppv, npv, f1 = prf(y_t, y_p)
    flag_rows.append({"domain": "ECHOCARDIOGRAPHY", "variable": v, "kappa": round(k, 4),
                      "kappa_lo": round(lo, 4), "kappa_hi": round(hi, 4),
                      "sens": round(sens, 4), "spec": round(spec, 4), "ppv": round(ppv, 4),
                      "npv": round(npv, 4), "f1": round(f1, 4), "n": len(y_t)})
# ef_value：数值一致性
ef_t = pd.to_numeric(g["F_ef_value"], errors="coerce") if "F_ef_value" in g.columns else None
if ef_t is None:
    g["F_ef_value"] = pd.to_numeric(g["A1_ef_value"].where(
        pd.to_numeric(g["A1_ef_value"], errors="coerce") == pd.to_numeric(g["A2_ef_value"], errors="coerce")),
        errors="coerce")
ef_t = pd.to_numeric(g["F_ef_value"], errors="coerce")
ef_p = pd.to_numeric(g["ext_ef"], errors="coerce")
both = ef_t.notna() & ef_p.notna()
r = float(np.corrcoef(ef_t[both], ef_p[both])[0, 1]) if both.sum() > 2 else np.nan
mad = float(np.mean(np.abs(ef_t[both] - ef_p[both]))) if both.sum() else np.nan
flag_rows.append({"domain": "ECHOCARDIOGRAPHY", "variable": "ef_value", "kappa": None,
                  "kappa_lo": None, "kappa_hi": None, "sens": None, "spec": None,
                  "ppv": None, "npv": None, "f1": None, "n": int(both.sum()),
                  "note": f"Pearson r={r:.3f}, MAD={mad:.1f} (n={int(both.sum())})"})
# 复合结局（binary abnormal；gold unreadable 行剔除并注明）
gold_unr = pd.to_numeric(g["F_echo_unreadable"], errors="coerce").fillna(0).to_numpy()
keep = gold_unr == 0
y_t = ((g["F_echo_normal"].astype(float) == 0) & (g["F_echo_variant"].astype(float) == 0) & keep).astype(int).to_numpy()
y_p = (g["ext_label"] == "abnormal").astype(int).to_numpy()
k = kappa(y_t[keep], y_p[keep])
lo, hi = boot_ci(y_t[keep], y_p[keep], kappa, persons[keep])
sens, spec, ppv, npv, f1 = prf(y_t[keep], y_p[keep])
comp_rows.append({"domain": "ECHOCARDIOGRAPHY", "composite": "abnormal (label-level, unreadable excluded)",
                  "n": int(keep.sum()), "kappa": round(k, 4), "kappa_lo": round(lo, 4),
                  "kappa_hi": round(hi, 4), "sens": round(sens, 4), "spec": round(spec, 4),
                  "ppv": round(ppv, 4), "npv": round(npv, 4), "f1": round(f1, 4)})
rl(f"ECHOCARDIOGRAPHY composite: κ={k:.3f} [{lo:.3f},{hi:.3f}] sens={sens:.3f} spec={spec:.3f} "
   f"(unreadable gold n={int((gold_unr==1).sum())} 剔除)")

# ================= ABDOMINAL_ULTRASOUND_PRIMARY =================
ABD_VARS = ["us_fatty", "us_hepatic_other", "us_gallstone", "us_kidney_cyst", "us_unreadable"]
g2, n_dis2, rf2 = resolve_final("ABDOMINAL_ULTRASOUND_PRIMARY", ABD_VARS, "A1_")
rl(f"ABDOMINAL_ULTRASOUND_PRIMARY：分歧格 {n_dis2}，rule-first {len(rf2)} {rf2[:5]}")
replay2 = [extract_abd(norm(t), "") for t in g2["text"].fillna("")]
g2["ext_fatty"] = [r["us_fatty"] for r in replay2]
g2["ext_other"] = [r["us_hepatic_other"] for r in replay2]
g2["ext_stone"] = [r["us_gallstone"] for r in replay2]
g2["ext_cyst"] = [r["us_kidney_cyst"] for r in replay2]
persons2 = g2["pseudo_id"].to_numpy()
for v, ext_col in [("us_fatty", "ext_fatty"), ("us_hepatic_other", "ext_other"),
                   ("us_gallstone", "ext_stone"), ("us_kidney_cyst", "ext_cyst")]:
    y_t = g2["F_" + v].astype(float).to_numpy()
    y_p = pd.to_numeric(g2[ext_col], errors="coerce").fillna(0).to_numpy()
    k = kappa(y_t, y_p)
    lo, hi = boot_ci(y_t, y_p, kappa, persons2)
    sens, spec, ppv, npv, f1 = prf(y_t, y_p)
    flag_rows.append({"domain": "ABDOMINAL_ULTRASOUND_PRIMARY", "variable": v, "kappa": round(k, 4),
                      "kappa_lo": round(lo, 4), "kappa_hi": round(hi, 4),
                      "sens": round(sens, 4), "spec": round(spec, 4), "ppv": round(ppv, 4),
                      "npv": round(npv, 4), "f1": round(f1, 4), "n": len(y_t)})
y_t2 = ((g2["F_us_fatty"].astype(float) == 1) | (g2["F_us_hepatic_other"].astype(float) == 1) |
        (g2["F_us_gallstone"].astype(float) == 1) | (g2["F_us_kidney_cyst"].astype(float) == 1)).astype(int).to_numpy()
y_p2 = ((pd.to_numeric(g2["ext_fatty"], errors="coerce").fillna(0) == 1) |
        (pd.to_numeric(g2["ext_other"], errors="coerce").fillna(0) == 1) |
        (pd.to_numeric(g2["ext_stone"], errors="coerce").fillna(0) == 1) |
        (pd.to_numeric(g2["ext_cyst"], errors="coerce").fillna(0) == 1)).astype(int).to_numpy()
k = kappa(y_t2, y_p2)
lo, hi = boot_ci(y_t2, y_p2, kappa, persons2)
sens, spec, ppv, npv, f1 = prf(y_t2, y_p2)
comp_rows.append({"domain": "ABDOMINAL_ULTRASOUND_PRIMARY", "composite": "any-abnormal (4 flags OR)", "n": len(y_t2),
                  "kappa": round(k, 4), "kappa_lo": round(lo, 4), "kappa_hi": round(hi, 4),
                  "sens": round(sens, 4), "spec": round(spec, 4), "ppv": round(ppv, 4),
                  "npv": round(npv, 4), "f1": round(f1, 4)})
rl(f"ABDOMINAL_ULTRASOUND_PRIMARY composite: κ={k:.3f} [{lo:.3f},{hi:.3f}] sens={sens:.3f} spec={spec:.3f}")

os.makedirs(OUT, exist_ok=True)
pd.DataFrame(flag_rows).to_csv(os.path.join(OUT, "wp1_external_site_performance.csv"),
                               index=False, encoding="utf-8-sig")
pd.DataFrame(comp_rows).to_csv(os.path.join(OUT, "wp1_external_site_composite.csv"),
                               index=False, encoding="utf-8-sig")
rl("\n注：ECHO LLM 轨（qwen2.5-14b, prompt v2.1）flag 级验收见 results/model_acceptance_echocardiography.csv（外部站点标注上执行）。"
   "ECG 主域外部标注 = external site 标注集。")
with open(os.path.join(OUT, "wp1_external_site_summary.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rep) + "\n")
rl("DONE")
