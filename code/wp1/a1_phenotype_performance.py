# -*- coding: utf-8 -*-
"""a1_phenotype_performance.py —— final three-class phenotype 性能（ECG 域 570）

目的：初代验收只验证 12 个 component flags（10/12），最终结局聚合规则从未报告临床性能。
     以金标准终值（ECG 570，含两轮仲裁）为参照，报告最终三类结局
     （normal/abnormal/unreadable）在 {naive, explicit} 两种聚合定义下的
     Sens/Spec/PPV/NPV/F1/κ + 95%CI（bootstrap B=1000，按 pseudo_id 聚类重抽），分年呈现。

定义（与冻结管线逐位同源）：
  naive (A)    ：ecg_unreadable==1→U；否则 ecg_normal==0→A；否则 N（= S/S anyabn 口径）
  explicit (B) ：ecg_unreadable==1→U；否则枚举 flags（af/pac_pvc/stt/rate/srirr/axis/
                 qwave_mi/avblock/bbb）任一==1→A；否则 N（= S v3_B 口径，V3.0 裁定采用）

金标准终值：A1==A2 直取；分歧行按「仲裁裁定_两轮」write-back；断言无未决分歧。
抽取侧：main.extract_ecg（Stage-4 扩展版）重放 gold 文本。

输出：results/wp1_final_phenotype_performance.csv（表型级长表）
     results/wp1_final_phenotype_flaglevel.csv（flag 级指标）
     results/wp1_final_phenotype_summary.txt
"""
import os
import sys

import numpy as np
import pandas as pd

ROOT = r"STUDY_ROOT"
OUT = os.path.join(ROOT, "results")
GOLD = os.path.join(ROOT, "data", "gold_standard_annotation_workbook_final.xlsx")
B = 1000
SEED = 20260921
ENUM = ["ecg_af", "ecg_pac_pvc", "ecg_stt", "ecg_rate", "ecg_srirr",
        "ecg_axis", "ecg_qwave_mi", "ecg_avblock", "ecg_bbb"]
FLAGS = ["ecg_normal", "ecg_af", "ecg_pac_pvc", "ecg_stt", "ecg_avblock", "ecg_bbb",
         "ecg_rate", "ecg_srirr", "ecg_axis", "ecg_qwave_mi", "ecg_other", "ecg_unreadable"]

sys.path.insert(0, os.path.join(ROOT, "code")); sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # deposited main.py in this package takes precedence
from main import extract_ecg, norm  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

rep = []


def rl(s=""):
    print(s, flush=True)
    rep.append(str(s))


rl("=== final three-class phenotype 性能（ECG 域 570）===")

# ---------- 1) 金标准终值 ----------
wb = pd.read_excel(GOLD, sheet_name="ECG", dtype=str)
arb = pd.read_excel(GOLD, sheet_name="仲裁裁定_两轮", dtype=str)
rl(f"gold ECG rows={len(wb)}  仲裁裁定_两轮 rows={len(arb)}")
ecg_arb = arb[arb["域"] == "ECG"]
rl(f"ECG 仲裁条数：{len(ecg_arb)}")

g = wb.copy()
# 终值解析（三层，权威来源逐级兜底）：
#  L1 逐变量裁定：「仲裁裁定_两轮」中 变量+sample_id 均在案（ecg_other 10 + ecg_rate 5）
#  L2 存量案级裁定：变量列为空、按 sample_id 案级裁定值write-back（11 条，各案恰 1 个分歧变量）
#  L3 rule-first 维持 A1：裁定理由明示规则归属（预期恰 3 格：ECG_0054/0514 stt、ECG_0341 avblock；
#     依据=同案裁定理由文本："早期复极属正常变异"/"左心室电压高非肥大"/"avblock/bbb各列均不覆盖"）
ecg_arb = arb[arb["域"] == "ECG"].copy()
var_ruling = ecg_arb[ecg_arb["变量"].notna()].set_index(["变量", "sample_id"])["仲裁裁定"]
case_ruling = ecg_arb[ecg_arb["变量"].isna()].set_index("sample_id")["仲裁裁定"]

unresolved = []
rule_first = []
n_dis = 0
for v in FLAGS:
    a1 = pd.to_numeric(g["A1_" + v], errors="coerce")
    a2 = pd.to_numeric(g["A2_" + v], errors="coerce")
    n_dis += int((a1 != a2).sum())
    fin = a1.where(a1 == a2)
    dis = fin.isna() & a1.notna() & a2.notna()
    for i in g.index[dis]:
        sid = g.at[i, "sample_id"]
        if (v, sid) in var_ruling.index:
            fin.at[i] = pd.to_numeric(var_ruling.loc[(v, sid)], errors="coerce")
        elif sid in case_ruling.index:
            fin.at[i] = pd.to_numeric(case_ruling.loc[sid], errors="coerce")
        else:
            fin.at[i] = a1.at[i]  # L3 维持 A1（裁定理由明示规则归属，逐格记录）
            rule_first.append(f"{v}:{sid}")
        if pd.isna(fin.at[i]):
            unresolved.append(f"{v}:{sid}")
    g["F_" + v] = fin
assert not unresolved, f"未决分歧：{unresolved}"
rl(f"分歧单元格总数：{n_dis}；其中 L1 逐变量裁定 + L2 存量案级裁定write-back：{n_dis - len(rule_first)}；"
   f"L3 rule-first 维持A1：{len(rule_first)} → {rule_first}")
assert len(rule_first) <= 3, "L3 数量超出预期（3），请人工复核裁定链"
for v in FLAGS:
    assert g["F_" + v].notna().all(), f"{v} 存在缺失终值"

# ---------- 2) 抽取侧重放 ----------
replay = []
for t in g["text"].fillna(""):
    f = extract_ecg(norm(t))
    if f.get("ecg_unreadable") == 1:
        replay.append({"ecg_unreadable": 1})
    else:
        replay.append(f)
ext = pd.DataFrame(replay)
ext["ecg_unreadable"] = pd.to_numeric(ext.get("ecg_unreadable", 0), errors="coerce").fillna(0)
for v in FLAGS:
    if v != "ecg_unreadable":
        ext[v] = pd.to_numeric(ext.get(v, 0), errors="coerce").fillna(0).astype(int)
    else:
        ext[v] = ext[v].astype(int)
ext = ext[FLAGS]
rl(f"抽取侧重放完成：{len(ext)} 行（unreadable={int(ext['ecg_unreadable'].sum())}）")


def three_class(flags_df, definition):
    un = flags_df["ecg_unreadable"].to_numpy()
    if definition == "naive":
        abn = flags_df["ecg_normal"].to_numpy() == 0
    else:
        abn = (flags_df[ENUM].sum(axis=1).to_numpy() > 0)
    return np.where(un == 1, "U", np.where(abn, "A", "N"))


gold_f = g[[("F_" + v) for v in FLAGS]].rename(columns={("F_" + v): v for v in FLAGS})
gold_f = gold_f.astype(int)
gold_naive = three_class(gold_f, "naive")
gold_expl = three_class(gold_f, "explicit")
ext_naive = three_class(ext, "naive")
ext_expl = three_class(ext, "explicit")
rl(f"金标三分类 naive：{pd.Series(gold_naive).value_counts().to_dict()}")
rl(f"金标三分类 explicit：{pd.Series(gold_expl).value_counts().to_dict()}")
rl(f"抽取三分类 naive：{pd.Series(ext_naive).value_counts().to_dict()}")
rl(f"抽取三分类 explicit：{pd.Series(ext_expl).value_counts().to_dict()}")

# ---------- 3) 指标 ----------
CLASSES = ["A", "N", "U"]
MET = ["sens", "spec", "ppv", "npv", "f1"]


def cohen_kappa(a, b):
    a, b = np.asarray(a), np.asarray(b)
    labs = sorted(set(a) | set(b))
    po = float(np.mean(a == b))
    pe = sum(float(np.mean(a == L)) * float(np.mean(b == L)) for L in labs)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


def one_v_one(y_true, y_pred, pos):
    y_t = (y_true == pos).astype(int)
    y_p = (y_pred == pos).astype(int)
    tp = int(((y_t == 1) & (y_p == 1)).sum())
    fp = int(((y_t == 0) & (y_p == 1)).sum())
    fn = int(((y_t == 1) & (y_p == 0)).sum())
    tn = int(((y_t == 0) & (y_p == 0)).sum())
    sens = tp / (tp + fn) if (tp + fn) else np.nan
    spec = tn / (tn + fp) if (tn + fp) else np.nan
    ppv = tp / (tp + fp) if (tp + fp) else np.nan
    npv = tn / (tn + fn) if (tn + fn) else np.nan
    f1 = (2 * ppv * sens / (ppv + sens)) if (sens == sens and ppv == ppv and (ppv + sens) > 0) else np.nan
    return sens, spec, ppv, npv, f1


persons = g["pseudo_id"].to_numpy()
uniq_p = pd.unique(persons)
p_idx = {p: np.where(persons == p)[0] for p in uniq_p}
rng = np.random.default_rng(SEED)
boot_idx = [np.concatenate([p_idx[p] for p in rng.choice(uniq_p, size=len(uniq_p), replace=True)])
            for _ in range(B)]

scopes = [("overall", np.ones(len(g), dtype=bool))] + [
    (str(y), (g["year"].astype(str) == str(y)).to_numpy())
    for y in sorted(g["year"].astype(str).unique())]

rows_main = []
preds = {"naive": ext_naive, "explicit": ext_expl}
golds = {"naive": gold_naive, "explicit": gold_expl}
for definition in ["naive", "explicit"]:
    yt_all, yp_all = golds[definition], preds[definition]
    for scope, mask in scopes:
        yt, yp = yt_all[mask], yp_all[mask]
        base = {"domain": "ECG", "definition": definition, "scope": scope, "n": int(mask.sum())}
        base["kappa_3class"] = round(cohen_kappa(yt, yp), 4)
        base["raw_agreement"] = round(float(np.mean(yt == yp)), 4)
        for pos in CLASSES:
            sens, spec, ppv, npv, f1 = one_v_one(yt, yp, pos)
            for m, val in zip(MET, [sens, spec, ppv, npv, f1]):
                base[f"{m}_{pos}"] = round(val, 4) if val == val else None
        bs = {m + "_" + pos: [] for pos in CLASSES for m in ["sens", "f1"]}
        bs["kappa_3class"] = []
        for bi in boot_idx:
            yb_t, yb_p = yt_all[bi], yp_all[bi]
            if len(set(yb_t) | set(yb_p)) < 2:
                continue
            bs["kappa_3class"].append(cohen_kappa(yb_t, yb_p))
            for pos in CLASSES:
                s, _, _, _, f1 = one_v_one(yb_t, yb_p, pos)
                bs["sens_" + pos].append(s)
                bs["f1_" + pos].append(f1)
        for k, arr in bs.items():
            arr = [x for x in arr if x == x]
            if arr:
                base[k + "_lo"] = round(float(np.percentile(arr, 2.5)), 4)
                base[k + "_hi"] = round(float(np.percentile(arr, 97.5)), 4)
        rows_main.append(base)
        rl(f"{definition:8s} {scope:8s} n={base['n']:4d} κ3={base['kappa_3class']:.3f} "
           f"sens_A={base['sens_A']} spec_A={base['spec_A']} f1_N={base['f1_N']} f1_U={base['f1_U']}")

# ---------- 4) flag 级 ----------
rows_flag = []
for v in FLAGS:
    xt = gold_f[v].to_numpy()
    xp = ext[v].to_numpy()
    if xp.sum() == 0 and xt.sum() == 0:
        continue
    for scope, mask in scopes:
        y_t, y_p = xt[mask], xp[mask]
        tp = int(((y_t == 1) & (y_p == 1)).sum())
        fp = int(((y_t == 0) & (y_p == 1)).sum())
        fn = int(((y_t == 1) & (y_p == 0)).sum())
        tn = int(((y_t == 0) & (y_p == 0)).sum())
        row = {"domain": "ECG", "variable": v, "scope": scope, "n": int(mask.sum()),
               "tp": tp, "fp": fp, "fn": fn, "tn": tn,
               "gold_pos": int(y_t.sum()), "ext_pos": int(y_p.sum())}
        row["raw_agreement"] = round(float(np.mean(y_t == y_p)), 4)
        row["kappa"] = round(cohen_kappa(y_t, y_p), 4)
        prec = tp / (tp + fp) if (tp + fp) else np.nan
        rec = tp / (tp + fn) if (tp + fn) else np.nan
        row["precision_1"] = round(prec, 4) if prec == prec else None
        row["recall_1"] = round(rec, 4) if rec == rec else None
        row["f1_1"] = round(2 * prec * rec / (prec + rec), 4) if (prec == prec and rec == rec and (prec + rec) > 0) else None
        rows_flag.append(row)

# ---------- 5) 落盘 ----------
os.makedirs(OUT, exist_ok=True)
pd.DataFrame(rows_main).to_csv(os.path.join(OUT, "wp1_final_phenotype_performance.csv"),
                               index=False, encoding="utf-8-sig")
pd.DataFrame(rows_flag).to_csv(os.path.join(OUT, "wp1_final_phenotype_flaglevel.csv"),
                               index=False, encoding="utf-8-sig")

rl("\n—— 互恰基准（供 wp1_audit 断言）——")
anchor = {"gold_rows": len(g), "flag_disputes_arbitrated": n_dis,
              "ext_unreadable": int(ext["ecg_unreadable"].sum())}
rl(str(anchor))
rl("注：flag 级 κ 可与 agreement_ECG.csv 互恰（v3 重放 vs 终值金标，口径=flag 层）")

with open(os.path.join(OUT, "wp1_final_phenotype_summary.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rep) + "\n")
rl("DONE")
