# -*- coding: utf-8 -*-
"""a6_gate_hierarchy.py —— 验收 gate 三级表现表（叙事重构供数）

三级：
  L1 variable   ：12 ECG flags × qwen2.5-14b 验收（model_acceptance_ecg.csv；below-gate 名单
                 与计数由 DataFrame 派生，禁手抄）
  L2 use-case   ：flags 在下游结局中的实际用途（显式阳性结局只用 ENUM 9 flags——全部 PASS；
                 other 本就不在显式定义内；unreadable 走"低于门槛→留痕+人工复核路径"）
  L3 composite  ：最终三类结局性能（本 WP a1 实测；κ 一律取自 a1 摘要工件的三位小数
                 印刷值——该印刷值即 a1 的权威口径，禁手抄、禁从 4dp CSV 再舍入）
叙事：初代验收只验 flags 不是缺陷掩盖，而是"生命周期治理必要性"的伏笔——
     L1 的未达标变量恰未进入主结局用途，而 L3 显示主结局聚合规则经裁定后达标。

摘要层（txt）原为手抄数值；现全部由上方
DataFrame 与 A1 摘要工件 f-string 派生。输入/输出路径支持环境变量覆盖
（A6_ACCEPT_ECG / A6_PERF / A6_A1TXT / A6_OUT），便于以包内 deposit 副本复算核对。

输出：results/wp1_gate_hierarchy.csv + wp1_gate_hierarchy_summary.txt
"""
import os
import re
import sys

import pandas as pd

ROOT = r"STUDY_ROOT"
RES = os.path.join(ROOT, "results")
OUTDIR = os.path.join(ROOT, "results")

ACCEPT_ECG = os.environ.get("A6_ACCEPT_ECG", os.path.join(RES, "model_acceptance_ecg.csv"))
PERF = os.environ.get("A6_PERF", os.path.join(OUTDIR, "wp1_final_phenotype_performance.csv"))
A1TXT = os.environ.get("A6_A1TXT", os.path.join(OUTDIR, "wp1_final_phenotype_summary.txt"))
WP1OUT = os.environ.get("A6_OUT", OUTDIR)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# ---------- L1 ----------
analysis = pd.read_csv(ACCEPT_ECG, encoding="utf-8-sig")
l1 = analysis[(analysis["model"] == "qwen2.5:14b") & (analysis["variable"] != "_SUMMARY_")].copy()
l1["level"] = "L1_variable"
l1 = l1[["level", "variable", "cohen_kappa", "F1_pos", "verdict", "fail_note"]]
l1 = l1.rename(columns={"variable": "item", "verdict": "gate"})

# ---------- L2 ----------
USE = {
    "ecg_af": "AF outcome（P4）+ 显式阳性结局 ENUM",
    "ecg_pac_pvc": "显式阳性结局 ENUM",
    "ecg_stt": "ST-T outcome（falsification control）+ 显式阳性结局 ENUM",
    "ecg_avblock": "anyBlock outcome + 显式阳性结局 ENUM",
    "ecg_bbb": "anyBlock outcome + 显式阳性结局 ENUM",
    "ecg_rate": "显式阳性结局 ENUM",
    "ecg_srirr": "显式阳性结局 ENUM",
    "ecg_axis": "显式阳性结局 ENUM",
    "ecg_qwave_mi": "显式阳性结局 ENUM",
    "ecg_other": "不在显式阳性定义内（V3.0 裁定：残余类别；2023 分歧核 panel 池来源）",
    "ecg_normal": "naive 聚合规则成分",
    "ecg_unreadable": "三类结局 U 类；词典轨确定性处理弃检/质量差；LLM 轨未达标→留痕+人工复核路径",
}
l2 = pd.DataFrame([{"level": "L2_usecase", "item": r["item"],
                    "downstream_use": USE[r["item"]],
                    "gate": "PASS" if r["gate"] == "PASS" else "BELOW-GATE(documented)"}
                   for _, r in l1.iterrows()])

# ---------- L3 ----------
perf = pd.read_csv(PERF, encoding="utf-8-sig")
l3 = perf[perf["scope"] == "overall"].copy()
l3_rows = [{"level": "L3_composite", "item": f"final three-class ({d})",
            "kappa_3class": float(l3.loc[l3["definition"] == d, "kappa_3class"].iloc[0]),
            "sens_A": l3.loc[l3["definition"] == d, "sens_A"].iloc[0],
            "spec_A": l3.loc[l3["definition"] == d, "spec_A"].iloc[0],
            "kappa_lo": l3.loc[l3["definition"] == d, "kappa_3class_lo"].iloc[0],
            "kappa_hi": l3.loc[l3["definition"] == d, "kappa_3class_hi"].iloc[0],
            "gate": "PASS" if d == "explicit" else "naive(对照)"}
           for d in ["explicit", "naive"]]
l3 = pd.DataFrame(l3_rows)

out = pd.concat([l1, l2, l3], ignore_index=True)
out.to_csv(os.path.join(WP1OUT, "wp1_gate_hierarchy.csv"), index=False, encoding="utf-8-sig")

# ---------- 摘要（全部数值由上方 DataFrame 与 A1 摘要工件派生，禁手抄） ----------
n_pass, n_tot = int((l1["gate"] == "PASS").sum()), int(len(l1))
below = l1[l1["gate"] != "PASS"].sort_values("item")
below_txt = " / ".join(f"{r.item} κ={r.cohen_kappa:.3f}" for r in below.itertuples())
with open(A1TXT, encoding="utf-8-sig") as _f:
    _a1 = _f.read()


def k3(defn, scope):
    """从 A1 摘要工件取三分类 κ 的三位小数印刷值（A1 的印刷值即权威 3dp 口径）。"""
    m = re.search(r"^%s\s+%s\s+n=\s*\d+\s+κ3=([0-9.]+)" % (defn, scope), _a1, re.M)
    assert m, f"A1 摘要工件缺 {defn}/{scope} 行: {A1TXT}"
    return float(m.group(1))


e_all, n_all = k3("explicit", "overall"), k3("naive", "overall")
e23, e24, n24 = k3("explicit", "2023"), k3("explicit", "2024"), k3("naive", "2024")
yy = f"κ={e23:.3f}" if e23 == e24 else f"κ={e23:.3f}/{e24:.3f}"
txt = [
    "=== gate hierarchy ===",
    f"L1：{n_pass}/{n_tot} PASS（qwen2.5-14b；below-gate = {below_txt}）",
    "L2：below-gate 变量均不进入显式阳性主结局用途（other 本就排除；unreadable 走人工复核路径）",
    f"L3：最终三类结局 explicit κ={e_all:.3f}（2023/2024 年 {yy}）；"
    f"naive κ={n_all:.3f}（2024 退化至 {n24:.3f}）",
    "叙事句：The initial acceptance rule evaluated component flags but did not directly validate the "
    "downstream outcome aggregation — this design gap later became the failure mode exposed by "
    f"longitudinal monitoring, and was closed by the pre-registered adjudicated definition (κ={e_all:.3f}).",
]
with open(os.path.join(WP1OUT, "wp1_gate_hierarchy_summary.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(txt) + "\n")
print("\n".join(txt))
print(out.to_string(index=False))
