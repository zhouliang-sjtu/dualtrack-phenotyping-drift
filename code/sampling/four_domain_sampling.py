# -*- coding: utf-8 -*-
"""four_domain_sampling.py —— 研究A（四域定义对齐判读）四域抽样 + 空白标注包生成

预注册依据：OSF 10.17605/OSF.IO/HGBN9（2026-09-21 17:48 提交，publicly registered）§3–§5、§8；
时序纪律：本脚本仅在注册 DOI 之后运行（ASSERT_OSF_DOI 门）。

设计（注册 §4）：
  每域确认性 n=140 = 决策/边界层 100（富集边界框随机，种子记录）
              + 确定性选定的 10 极端异常 + 10 极端正常（规则选取，reference key held by the arbiter，release 前建）
              + 对照 20（边界层外随机；ECG=2021 稳定年，primary 域=全框，ABD_HOSPITAL=逐年比例分配）
  另每域 pilot 20 单独抽取（仅作手册校准，不进确证分析）。
排除（§3/§8）：金标准 1,470（gold_* 按键）、首次仲裁 170（stage2_linkage）、
              内部开发仲裁 160（adjudication_160_linkage）之记录一律不入任何层；
              person-wave 键框阶段去重。

四域抽样框：
  ECG  (hospital)   决策边界框 = 2023 定义分歧核（naive 阳性 & enumerated 阴性 & 非 unreadable；预排除前 3,204，
             复算自 analysis_frame + v3_flags_cache，与 primary 分析口径一致）；对照 = 2021 核外稳定记录。
  ECHO (primary)  框 = 600 报告父框（data/reference_standard/echo_full.csv）− 参考标准 300；边界富集 = EF 45–55 ∨ 左房内径 38–42
             ∨ 少量/轻度/轻微返流 ∨ normal-variant（label=normal_variant）。
  ABD_PRIMARY      框 = 600 父框（data/abdominal_ultrasound_primary.csv）− 金标准 300；边界富集 = 描述式脂肪肝单要素（细密无衰减、
             衰减/欠清无细密）∨ 程度词含糊（无分级/复合分级/倾向性措辞）∨ 肝内未定性结节≥20mm ∨ 回声不均(U3)。
  ABD_HOSPITAL  (hospital)  框 = hospital 队列腹部超声全框（hospital_ultrasound_text_long，2018–2024 含 2020 全描述性 wave，us_text+main_text）
             − 金标准 300；边界富集同 ABD_PRIMARY；对照逐年比例分配（最大余数法，非空年≥1）。

确定性选取规则（记录于 summary；仲裁员据此在分发前建reference key）：
  ECG   异常 = 9 枚举 flag 计数降序 → 文本长度降序 → id/year 升序（计数≥3 不足则降为 ≥2/≥1）；
        正常 = v3 normal==1 且 9 枚举全 0 且非 unreadable → 文本长度降序 → id/year 升序。
  ECHO  异常 = 结构异常计分（lvh+la_dilate+EF<50+中重度返流+节律）降序 → EF 升序 → 长度 → id；
        正常 = label=normal 且 EF≥60 且左房<38 且无返流 → 长度降序 → id。
  abdominal ultrasound 异常 = flag 计数（fatty+hepatic_other+gallstone+kidney_cyst+重度）降序 → 长度 → id；
        正常 = 全 0 且含"正常/未见异常" → 长度降序 → id。

盲法（手册 v2.1 附录 F.1-3）：标注员可见文件仅含 sample_id（域内中性乱序编号）+ 文本 + 空白列；
  年份/检查日期/伪标识/层别/机器 flags 一律只在 sampling/ 内部连接表中（fingerprinted in the release manifest and not distributed）。

种子：SEED_SAMPLE=20260922（抽样），SEED_BOOTSTRAP=20260922（下游 CI 重抽样，预先登记）。
输出：
  sampling/four_domain_sampling_summary.txt        全程日志 + 指纹
  sampling/frames/<DOM>_frame.csv                  各域全框（无文本列；含层标记与抽中 sample_id）
  sampling/external_site_linkage_key.csv                    sample_id ↔ 层别 ↔ 键（内部）
  sampling/workbook_text_hashes.csv                抽中文本 SHA256（可溯源性核验）
  01-blind-annotation/DA_<DOM>_to_annotate_主表.csv / _主表.xlsx / _A1.csv / _A2.csv
  01-blind-annotation/DA_<DOM>_pilot20_主表.csv                （pilot 与确认层分文件）
"""
import hashlib
import os
import re
import sys

import numpy as np
import pandas as pd

ROOT = r"STUDY_ROOT"
OUT = os.path.join(ROOT, "reference-data", "dataset", "02-四域定义对齐判读")
FROZEN_CODE = os.path.join(ROOT, "code")

# ---------- ASSERT_OSF_DOI：研究A确认性抽样执行门（注册 §4：抽样仅在 DOI 之后） ----------
OSF_DOI = "10.17605/OSF.IO/HGBN9"  # 2026-09-21 17:48 提交，当晚made Public
if not OSF_DOI.startswith("10."):
    raise SystemExit("[ASSERT_OSF_DOI] 研究A四域抽样必须在 OSF 注册获得 DOI 之后执行。"
                     "注册：osf-preregistration/")

SEED_SAMPLE = 20260922          # 新种子（superseded预抽 20260921 之后）
SEED_BOOTSTRAP = 20260922       # 下游 CI bootstrap 种子（预先登记，成对披露）
N_DECISION, N_ANCHOR, N_CONTROL, N_PILOT = 100, 10, 20, 20

sys.path.insert(0, FROZEN_CODE); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # deposited frozen main.py (sampling/) takes precedence
from main import extract_abd, extract_echo, norm  # noqa: E402  冻结管线（SHA256 见 summary）

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

rep = []


def rl(s=""):
    print(s, flush=True)
    rep.append(str(s))


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tsha(t):
    return hashlib.sha256(str(t).encode("utf-8")).hexdigest()[:16]


rng = np.random.default_rng(SEED_SAMPLE)

# ================= 排除键 =================
D = os.path.join(ROOT, "data")
gold_ecg = pd.read_csv(os.path.join(D, "reference_standard", "ecg_full.csv"), encoding="utf-8-sig", dtype=str)
gold_echo = pd.read_csv(os.path.join(D, "reference_standard", "echo_300.csv"), encoding="utf-8-sig", dtype=str)
gold_abdp = pd.read_csv(os.path.join(D, "reference_standard", "abdomen_primary_300.csv"), encoding="utf-8-sig", dtype=str)
gold_abdh = pd.read_csv(os.path.join(D, "reference_standard", "abdomen_hospital_300.csv"), encoding="utf-8-sig", dtype=str)
excl_ecg = set(gold_ecg["id"].fillna("").str.strip() + "|" + gold_ecg["year"].fillna("").str.strip())
excl_echo = set(gold_echo["id"].fillna("").str.strip() + "|" + gold_echo["exam_date"].fillna("").str.strip())
excl_abdp = set(gold_abdp["id"].fillna("").str.strip() + "|" + gold_abdp["exam_date"].fillna("").str.strip())
excl_abdh = set(gold_abdh["id"].fillna("").str.strip() + "|" + gold_abdh["year"].fillna("").str.strip())
# 170（首次尝试）与 160（内部开发仲裁）——均为 ECG 域记录
l170 = pd.read_csv(os.path.join(ROOT, "results", "stage2_linkage.csv"),
                   encoding="utf-8-sig", dtype=str)
l160 = pd.read_csv(os.path.join(ROOT, "reference-data", "reference-data",
                                "05-supplementary-annotation-and-realignment",
                                "adjudication_160_linkage.csv"), encoding="utf-8-sig", dtype=str)
excl_ecg |= set(l170["id"].fillna("").str.strip() + "|" + l170["year"].fillna("").str.strip())
excl_ecg |= set(l160["id"].fillna("").str.strip() + "|" + l160["year"].fillna("").str.strip())
rl("=== 研究A 四域抽样（OSF 10.17605/OSF.IO/HGBN9 之后执行）===")
rl(f"种子：sample={SEED_SAMPLE}  bootstrap={SEED_BOOTSTRAP}")
rl(f"排除键：gold_ecg={len(gold_ecg)}  gold_echo={len(gold_echo)}  gold_abdp={len(gold_abdp)}  "
   f"gold_abdh={len(gold_abdh)}  trial170={len(l170)}  trial160={len(l160)}"
   f"  → excl_ecg 总={len(excl_ecg)}")

link_rows = []      # 内部连接表
text_hashes = []    # 抽中文本哈希
selected_texts = []  # PII 扫描用（各域抽中文本）
FLAG9 = ["ecg_af", "ecg_pac_pvc", "ecg_stt", "ecg_rate", "ecg_srirr",
         "ecg_axis", "ecg_qwave_mi", "ecg_avblock", "ecg_bbb"]


def alloc(strata_counts, n_total):
    """最大余数法比例分配，非空层至少 1。"""
    N = strata_counts.sum()
    raw = strata_counts / N * n_total
    base = np.floor(raw).astype(int)
    base = np.maximum(base, 1)
    diff = n_total - base.sum()
    frac = (raw - np.floor(raw)).sort_values(ascending=False)
    keys = list(frac.index)
    i = 0
    while diff != 0:
        k = keys[i % len(keys)]
        if diff > 0:
            base[k] += 1
            diff -= 1
        elif base[k] > 1:
            base[k] -= 1
            diff += 1
        i += 1
        if i > 10000:
            raise RuntimeError("alloc failed")
    return base


def register(df, domain, stratum_map):
    """登记抽中记录：内部连接 + 文本哈希。stratum_map: sample_id -> stratum。"""
    for _, r in df.iterrows():
        link_rows.append({
            "domain": domain, "sample_id": r["sample_id"],
            "stratum": stratum_map[r["sample_id"]],
            "record_key": r["_key"], "year_or_date": r.get("_yord", ""),
            "text_len": len(str(r.get("text", ""))),
            "text_sha16": tsha(r.get("text", ""))})


def neutralize(domain, sel_df, stratum_map):
    """盲法重塑（F.1-3：包内不含层别）：确认层乱序后赋予中性编号 <DOM>-001..140；
    pilot 保留 <DOM>-P01..20（pilot 校准本身是公开环节）。旧 id→新 id 映射不落盘，
    层别仅存 external_site_linkage_key（内部件）。"""
    col = sel_df["sample_id"]
    is_pilot = col.str.contains(r"-P\d{2}$").values
    conf = sel_df[~is_pilot].sample(frac=1.0, random_state=rng)
    pilo = sel_df[is_pilot].sort_values("sample_id")
    old_ids = conf["sample_id"].tolist() + pilo["sample_id"].tolist()
    new_ids = ([f"{domain}-{i+1:03d}" for i in range(len(conf))]
               + [f"{domain}-P{i+1:02d}" for i in range(len(pilo))])
    mapping = dict(zip(old_ids, new_ids))
    out = pd.concat([conf, pilo])
    out["sample_id"] = [mapping[v] for v in out["sample_id"]]
    new_stratum = {mapping[k]: v for k, v in stratum_map.items()}
    return out, new_stratum, mapping


def build_workbooks(domain, sel, flag_vars):
    """sel: DataFrame(sample_id 列, 含 text)。CSV 单格式（2026-09-22 用户指令：不生成 xlsx，
    A1/A2 同表分栏，由用户向标注员交代填写范围）。盲法：仅 sample_id + text + 空白列（F.1-3）。"""
    wd = os.path.join(OUT, "01-blind-annotation")
    os.makedirs(wd, exist_ok=True)
    annot_cols = []
    for a in ("A1", "A2"):
        annot_cols += [f"{a}_{v}" for v in flag_vars]
        annot_cols += [f"{a}_outcome", f"{a}_abnormal_basis", f"{a}_uninterp_reason", f"{a}_note"]

    def mk(df):
        m = pd.DataFrame({"sample_id": df["sample_id"].values, "text": df["text"].values})
        for c in annot_cols:
            m[c] = ""
        m["arbitration"] = ""
        return m

    is_pilot = sel["sample_id"].str.contains(r"-P\d{2}$").values
    master = mk(sel[~is_pilot])          # 确认层 140（A1/A2 同表）
    pilot = mk(sel[is_pilot])            # pilot 20（A1/A2 同表）
    main_path = os.path.join(wd, f"DA_{domain}_to_annotate.csv")
    master.to_csv(main_path, index=False, encoding="utf-8-sig")
    pilot.to_csv(os.path.join(wd, f"DA_{domain}_pilot20.csv"), index=False, encoding="utf-8-sig")
    # 断言盲法：不含年份/键/层别/机器列；确认层不含 pilot
    forbidden = {"year", "exam_date", "pseudo_id", "id", "stratum", "ef", "label"}
    hit = forbidden & set(master.columns)
    assert not hit, f"盲法违例列：{hit}"
    assert not master["sample_id"].str.contains("-P").any(), "确认层混入 pilot"
    return main_path


# ================= 域① ECG (hospital) =================
rl("\n—— 域① ECG（hospital）——")
BASE3 = r"STUDY_ROOT/study-data-root/data/processed"
ha = pd.read_csv(os.path.join(BASE3, "analysis_frame.csv"), encoding="utf-8-sig",
                 dtype={"id": str, "year": str, "ecg_text": str}, low_memory=False)
ha = ha.sort_values(["id", "year"]).reset_index(drop=True)
cache = pd.read_csv(os.path.join(ROOT, "results", "v3_flags_cache.csv.gz"), encoding="utf-8-sig")
assert len(cache) == len(ha), f"缓存行数 {len(cache)} != analysis_frame {len(ha)}，请先重建缓存"
for c in cache.columns:
    ha[c] = cache[c].to_numpy()
ha["ecg_text"] = ha["ecg_text"].fillna("")
for c in ["v3_ecg_normal", "v3_ecg_unreadable"] + [f"v3_{f}" for f in FLAG9]:
    ha[c] = pd.to_numeric(ha[c], errors="coerce").fillna(0).astype(int)
ha["_key"] = ha["id"].str.strip() + "|" + ha["year"].str.strip()
ha["sample_id"] = ""
ha["A"] = ((ha["v3_ecg_normal"] == 0) & (ha["v3_ecg_unreadable"] == 0)).astype(int)
ha["B"] = (ha[[f"v3_{f}" for f in FLAG9]].max(axis=1)).astype(int)
core_all = ha[(ha["year"] == "2023") & (ha["A"] == 1) & (ha["B"] == 0)
              & (ha["ecg_text"].str.strip() != "")]  # 分析口径：文本非空（缓存空行 flags=0,0 不算 naive 阳性）
rl(f"2023 分歧核（预排除）：{len(core_all)}（注册口径 3,204）")
assert len(core_all) == 3204, f"2023 分歧核 {len(core_all)} != 3,204，口径漂移，停止"
core = core_all[~core_all["_key"].isin(excl_ecg) & (core_all["ecg_text"].str.strip() != "")].copy()
rl(f"决策边界框（排除后）：{len(core)}")
stratum = {}
# pilot 20 → decision 100（同框先后抽取，无放回；赋值统一写回 ha 主帧）
p_idx = core.sample(n=N_PILOT, random_state=rng).index
ha.loc[p_idx, "sample_id"] = [f"ECG-P{i+1:02d}" for i in range(N_PILOT)]
for i, ix in enumerate(p_idx):
    stratum[f"ECG-P{i+1:02d}"] = "pilot"
d_idx = core[~core.index.isin(p_idx)].sample(n=N_DECISION, random_state=rng).index
ha.loc[d_idx, "sample_id"] = [f"ECG-{i+1:03d}" for i in range(N_DECISION)]
for i, ix in enumerate(d_idx):
    stratum[f"ECG-{i+1:03d}"] = "decision"
rl(f"pilot=20 decision=100")
# 确定性选取（确定性，全域合格池 = 全年非排除、有文本、非 unreadable、未抽中）
elig = ha[(~ha["_key"].isin(excl_ecg)) & (ha["ecg_text"].str.strip() != "")
          & (ha["v3_ecg_unreadable"] == 0) & (ha["sample_id"] == "")].copy()
elig["flen"] = elig["ecg_text"].str.len()
abn = elig.copy()
abn["nscore"] = abn[[f"v3_{f}" for f in FLAG9]].sum(axis=1)
abn = abn[abn["nscore"] >= 3] if (abn["nscore"] >= 3).sum() >= N_ANCHOR else abn[abn["nscore"] >= 2]
abn = abn.sort_values(["nscore", "flen", "id", "year"], ascending=[False, False, True, True]).head(N_ANCHOR)
nor = elig[(elig["v3_ecg_normal"] == 1) &
           (elig[[f"v3_{f}" for f in FLAG9]].max(axis=1) == 0)]
nor = nor.sort_values(["flen", "id", "year"], ascending=[False, True, True]).head(N_ANCHOR)
assert len(abn) == N_ANCHOR and len(nor) == N_ANCHOR, f"ECG 选取不足：abn={len(abn)} nor={len(nor)}"
for i, (_, r) in enumerate(abn.iterrows()):
    sid = f"ECG-AB{i+1:02d}"
    ha.loc[r.name, "sample_id"] = sid
    stratum[sid] = "anchor_abnormal"
for i, (_, r) in enumerate(nor.iterrows()):
    sid = f"ECG-AN{i+1:02d}"
    ha.loc[r.name, "sample_id"] = sid
    stratum[sid] = "anchor_normal"
rl(f"anchors: AB 10（最高 flag 计数={int(abn['nscore'].max())}） AN 10")
# 对照：2021 稳定年、核外、非 unreadable、未抽中
c_pool = ha[(ha["year"] == "2021") & (~ha["_key"].isin(excl_ecg))
            & (ha["ecg_text"].str.strip() != "") & (ha["v3_ecg_unreadable"] == 0)
            & ~((ha["A"] == 1) & (ha["B"] == 0)) & (ha["sample_id"] == "")]
c_idx = c_pool.sample(n=N_CONTROL, random_state=rng).index
ha.loc[c_idx, "sample_id"] = [f"ECG-C{i+1:02d}" for i in range(N_CONTROL)]
for i, ix in enumerate(c_idx):
    stratum[f"ECG-C{i+1:02d}"] = "control"
sel_ecg = ha[ha["sample_id"] != ""].copy()
assert len(sel_ecg) == 160, f"ECG 抽中数 {len(sel_ecg)} != 160"
sel_ecg["_key"] = sel_ecg["id"].str.strip() + "|" + sel_ecg["year"].str.strip()
sel_ecg["_yord"] = sel_ecg["year"]
sel_ecg["text"] = sel_ecg["ecg_text"]
rl(f"ECG 抽中合计：{len(sel_ecg)}（层分布：{pd.Series(stratum).value_counts().to_dict()}）")
sel_ecg, stratum, idmap = neutralize("ECG", sel_ecg, stratum)
ha["sample_id"] = ha["sample_id"].map(lambda v: idmap.get(v, v))
register(sel_ecg, "ECG", stratum)
selected_texts += sel_ecg["text"].tolist()
text_hashes += [{"domain": "ECG", "sample_id": r["sample_id"], "text_sha16": tsha(r["text"])}
                for _, r in sel_ecg.iterrows()]
ECG_VARS = ["ecg_normal", "ecg_af", "ecg_pac_pvc", "ecg_stt", "ecg_avblock", "ecg_bbb",
            "ecg_rate", "ecg_srirr", "ecg_axis", "ecg_qwave_mi", "ecg_other", "ecg_unreadable"]
build_workbooks("ECG", sel_ecg, ECG_VARS)
frame_ecg = ha[["id", "year", "A", "B", "v3_ecg_normal", "v3_ecg_unreadable"] +
               [f"v3_{f}" for f in FLAG9] + ["sample_id"]].copy()
os.makedirs(os.path.join(OUT, "sampling", "frames"), exist_ok=True)
frame_ecg.to_csv(os.path.join(OUT, "sampling", "frames", "ECG_frame.csv"),
                 index=False, encoding="utf-8-sig")

# ================= 域② ECHO (primary) =================
rl("\n—— 域② ECHO（primary）——")
src_echo = pd.read_csv(os.path.join(D, "reference_standard", "echo_full.csv"), encoding="utf-8-sig", dtype=str)
gold_echo_ids = set(gold_echo["sample_id"].fillna("").str.strip())
fr = src_echo[~src_echo["sample_id"].isin(gold_echo_ids)].copy()
fr = fr[fr["text"].fillna("").str.strip() != ""]
fr["_key"] = fr["id"].fillna("").str.strip() + "|" + fr["exam_date"].fillna("").str.strip()
fr = fr[~fr["_key"].isin(excl_echo)]
rl(f"框：父框 600 − gold 300 − 空/排除 = {len(fr)}")
E = pd.DataFrame([extract_echo(norm(t)) for t in fr["text"]])
fr = pd.concat([fr.reset_index(drop=True), E.reset_index(drop=True)], axis=1)
fr["la_mm"] = fr["text"].map(lambda t: (lambda m: float(m.group(1)) if m else None)(
    re.search(r"左房内径[^0-9]{0,4}(\d{2,3})", str(t))))
fr["abn_score"] = (fr["lvh"] + fr["la_dilate"] + fr["rhythm"]
                   + fr["reflux_grade"].isin(["moderate", "severe"]).astype(int)
                   + ((fr["ef"].notna()) & (fr["ef"] < 50)).astype(int))
boundary = ((fr["ef"].notna() & (fr["ef"] >= 45) & (fr["ef"] <= 55))
            | (fr["la_mm"].notna() & (fr["la_mm"] >= 38) & (fr["la_mm"] <= 42))
            | (fr["reflux_grade"] == "mild") | (fr["label"] == "normal_variant"))
rl(f"边界富集池：{int(boundary.sum())} / {len(fr)}"
   f"（EF45-55={int((fr['ef'].notna() & (fr['ef']>=45) & (fr['ef']<=55)).sum())}, "
   f"LA38-42={int((fr['la_mm'].notna() & (fr['la_mm']>=38) & (fr['la_mm']<=42)).sum())}, "
   f"mild_reflux={int((fr['reflux_grade']=='mild').sum())}, variant={int((fr['label']=='normal_variant').sum())}）")
fr["sample_id"] = ""
stratum = {}
bp = fr[boundary.values]
p_idx = bp.sample(n=min(N_PILOT, len(bp)), random_state=rng).index
fr.loc[p_idx, "sample_id"] = [f"ECHO-P{i+1:02d}" for i in range(len(p_idx))]
for i, ix in enumerate(p_idx):
    stratum[f"ECHO-P{i+1:02d}"] = "pilot"
rest_b = fr[(fr["sample_id"] == "") & boundary]
d_idx = rest_b.sample(n=min(N_DECISION, len(rest_b)), random_state=rng).index
fr.loc[d_idx, "sample_id"] = [f"ECHO-{i+1:03d}" for i in range(len(d_idx))]
for i, ix in enumerate(d_idx):
    stratum[f"ECHO-{i+1:03d}"] = "decision"
rl(f"pilot={len(p_idx)} decision={len(d_idx)}")
elig = fr[(fr["sample_id"] == "")].copy()
elig["flen"] = elig["text"].str.len()
abn = elig[elig["abn_score"] >= 2] if (elig["abn_score"] >= 2).sum() >= N_ANCHOR else elig[elig["abn_score"] >= 1]
abn = abn.sort_values(["abn_score", "ef", "flen", "id"],
                      ascending=[False, True, False, True]).head(N_ANCHOR)
nor = elig[(elig["label"] == "normal") & (elig["ef"].notna()) & (elig["ef"] >= 60)
           & ((elig["la_mm"].isna()) | (elig["la_mm"] < 38)) & (elig["reflux_grade"] == "none")]
nor = nor.sort_values(["flen", "id"], ascending=[False, True]).head(N_ANCHOR)
assert len(abn) == N_ANCHOR and len(nor) == N_ANCHOR, f"ECHO 选取不足：abn={len(abn)} nor={len(nor)}"
for i, (_, r) in enumerate(abn.iterrows()):
    fr.loc[r.name, "sample_id"] = f"ECHO-AB{i+1:02d}"
    stratum[f"ECHO-AB{i+1:02d}"] = "anchor_abnormal"
for i, (_, r) in enumerate(nor.iterrows()):
    fr.loc[r.name, "sample_id"] = f"ECHO-AN{i+1:02d}"
    stratum[f"ECHO-AN{i+1:02d}"] = "anchor_normal"
c_pool = fr[(fr["sample_id"] == "") & (~boundary)]
c_idx = c_pool.sample(n=N_CONTROL, random_state=rng).index
fr.loc[c_idx, "sample_id"] = [f"ECHO-C{i+1:02d}" for i in range(N_CONTROL)]
for i, ix in enumerate(c_idx):
    stratum[f"ECHO-C{i+1:02d}"] = "control"
sel = fr[fr["sample_id"] != ""].copy()
sel["_yord"] = sel["exam_date"]
rl(f"ECHO 抽中合计：{len(sel)}（层分布：{pd.Series(stratum).value_counts().to_dict()}）")
sel, stratum, idmap = neutralize("ECHO", sel, stratum)
fr["sample_id"] = fr["sample_id"].map(lambda v: idmap.get(v, v))
register(sel, "ECHO", stratum)
selected_texts += sel["text"].tolist()
text_hashes += [{"domain": "ECHO", "sample_id": r["sample_id"], "text_sha16": tsha(r["text"])}
                for _, r in sel.iterrows()]
ECHO_VARS = ["echo_normal", "echo_variant", "echo_lvh", "echo_la_dilate", "ef_value",
             "ef_abnormal", "reflux_grade", "echo_rhythm", "echo_unreadable"]
build_workbooks("ECHO", sel, ECHO_VARS)
fr_out = fr.copy()
for c in ["label", "lvh", "la_dilate", "ef", "reflux_grade", "rhythm", "abn_score", "la_mm"]:
    fr_out[c] = fr_out[c].astype(str)
fr_out[["sample_id", "id", "exam_date", "label", "lvh", "la_dilate", "ef", "la_mm",
        "reflux_grade", "rhythm", "abn_score"]].to_csv(
    os.path.join(OUT, "sampling", "frames", "ECHO_frame.csv"), index=False, encoding="utf-8-sig")

# ================= 域③④ 腹部超声公共富集规则 =================
RE_LESION = re.compile(r"(结节|占位|团块)[^。；\n]{0,30}?(?:约)?(\d{2,3}(?:\.\d)?)\s*(mm|cm)")
RE_U3 = re.compile(r"回声不均|不均匀|非均匀|局限性|局灶")
RE_DEG_VAR = re.compile(r"轻\s*[-~到]\s*中|中\s*[-~到]\s*重|倾向|考虑|待排|可能")


def abd_boundary(t, main_text, flags):
    """ABD_PRIMARY/ABD_HOSPITAL 共用边界富集（确定性；定义见文件头）。"""
    t = str(t or "")
    e1 = "细密" in t
    e2 = bool(re.search(r"衰减|欠清", t))
    partial = (e1 != e2) or (not e1 and not e2 and bool(re.search(r"管道[^。；\n]{0,4}欠清", t)))
    fatty = flags["us_fatty"] == 1
    deg = str(flags.get("us_fatty_degree", "") or "")
    deg_var = fatty and (deg == "" or bool(RE_DEG_VAR.search(t)))
    lesion = False
    for m in RE_LESION.finditer(t):
        v = float(m.group(2))
        if (m.group(3) == "cm" and v >= 2.0) or (m.group(3) == "mm" and v >= 20):
            lesion = True
            break
    u3 = bool(RE_U3.search(t))
    return bool(partial or deg_var or lesion or u3), {
        "partial_desc": partial, "degree_variant": deg_var, "lesion_ge20": lesion, "u3": u3}


def abd_anchors(fr, prefix):
    fr = fr.copy()
    fr["flen"] = fr["text"].str.len()
    fr["nscore"] = (fr["us_fatty"] + fr["us_hepatic_other"] + fr["us_gallstone"]
                    + fr["us_kidney_cyst"] + (fr["us_fatty_degree"] == "重度").astype(int))
    abn = fr[fr["nscore"] >= 2] if (fr["nscore"] >= 2).sum() >= N_ANCHOR else fr[fr["nscore"] >= 1]
    abn = abn.sort_values(["nscore", "flen", "id"], ascending=[False, False, True]).head(N_ANCHOR)
    nor = fr[(fr["us_fatty"] == 0) & (fr["us_hepatic_other"] == 0) & (fr["us_gallstone"] == 0)
             & (fr["us_kidney_cyst"] == 0)
             & fr["text"].str.contains("正常|未见异常|未见明显异常", regex=True)]
    nor = nor.sort_values(["flen", "id"], ascending=[False, True]).head(N_ANCHOR)
    assert len(abn) == N_ANCHOR and len(nor) == N_ANCHOR, f"{prefix} 选取不足"
    return abn, nor


# ================= 域③ abdominal ultrasound (primary) =================
rl("\n—— 域③ abdominal ultrasound（primary）——")
src_abdp = pd.read_csv(os.path.join(D, "reference_standard", "abdomen_primary_full.csv"), encoding="utf-8-sig", dtype=str)
gold_abdp_ids = set(gold_abdp["sample_id"].fillna("").str.strip())
frp = src_abdp[~src_abdp["sample_id"].isin(gold_abdp_ids)].copy()
frp = frp[frp["text"].fillna("").str.strip() != ""]
frp["_key"] = frp["id"].fillna("").str.strip() + "|" + frp["exam_date"].fillna("").str.strip()
frp = frp[~frp["_key"].isin(excl_abdp)]
# 2026-09-22 用户决策（污染甄别报告 §二/§三）：追加文本级去重——与 gold300 文本（规范化）逐字
# 一致的记录不入框，杜绝"gold 内容换皮进入验证包"的盲法记忆风险。ECG 域模板文本豁免（见报告）。
_nt = lambda t: re.sub(r"\s+", "", str(t or ""))
_gold_abdp_ntext = {_nt(t) for t in gold_abdp["text"]}
_n0 = len(frp)
frp = frp[~frp["text"].map(lambda t: _nt(t) in _gold_abdp_ntext)].copy()
rl(f"框：父框 600 − gold 300 − 空/排除 = {_n0}；文本级去重（与 gold300 逐字一致）后 = {len(frp)}")
A = pd.DataFrame([extract_abd(norm(t)) for t in frp["text"]])
frp = pd.concat([frp.reset_index(drop=True), A.reset_index(drop=True)], axis=1)
bd = frp.apply(lambda r: abd_boundary(r["text"], "", r)[0], axis=1)
rl(f"边界富集池：{int(bd.sum())} / {len(frp)}")
frp["sample_id"] = ""
stratum = {}
bp = frp[bd.values]
p_idx = bp.sample(n=min(N_PILOT, len(bp)), random_state=rng).index
frp.loc[p_idx, "sample_id"] = [f"ABDP-P{i+1:02d}" for i in range(len(p_idx))]
for i, ix in enumerate(p_idx):
    stratum[f"ABDP-P{i+1:02d}"] = "pilot"
rest_b = frp[(frp["sample_id"] == "") & bd.values]
d_idx = rest_b.sample(n=min(N_DECISION, len(rest_b)), random_state=rng).index
frp.loc[d_idx, "sample_id"] = [f"ABDP-{i+1:03d}" for i in range(len(d_idx))]
for i, ix in enumerate(d_idx):
    stratum[f"ABDP-{i+1:03d}"] = "decision"
rl(f"pilot={len(p_idx)} decision={len(d_idx)}")
elig = frp[frp["sample_id"] == ""].copy()
elig["us_fatty_degree"] = elig["us_fatty_degree"].fillna("")
abn, nor = abd_anchors(elig, "ABDP")
for i, (_, r) in enumerate(abn.iterrows()):
    frp.loc[r.name, "sample_id"] = f"ABDP-AB{i+1:02d}"
    stratum[f"ABDP-AB{i+1:02d}"] = "anchor_abnormal"
for i, (_, r) in enumerate(nor.iterrows()):
    frp.loc[r.name, "sample_id"] = f"ABDP-AN{i+1:02d}"
    stratum[f"ABDP-AN{i+1:02d}"] = "anchor_normal"
c_pool = frp[(frp["sample_id"] == "") & (~bd)]
c_idx = c_pool.sample(n=N_CONTROL, random_state=rng).index
frp.loc[c_idx, "sample_id"] = [f"ABDP-C{i+1:02d}" for i in range(N_CONTROL)]
for i, ix in enumerate(c_idx):
    stratum[f"ABDP-C{i+1:02d}"] = "control"
sel = frp[frp["sample_id"] != ""].copy()
sel["_yord"] = sel["exam_date"]
rl(f"ABDP 抽中合计：{len(sel)}（层分布：{pd.Series(stratum).value_counts().to_dict()}）")
sel, stratum, idmap = neutralize("ABD_PRIMARY", sel, stratum)
frp["sample_id"] = frp["sample_id"].map(lambda v: idmap.get(v, v))
register(sel, "ABD_PRIMARY", stratum)
selected_texts += sel["text"].tolist()
text_hashes += [{"domain": "ABD_PRIMARY", "sample_id": r["sample_id"], "text_sha16": tsha(r["text"])}
                for _, r in sel.iterrows()]
ABD_VARS = ["us_fatty", "us_fatty_degree", "us_hepatic_other", "us_gallstone",
            "us_kidney_cyst", "us_unreadable"]
build_workbooks("ABD_PRIMARY", sel, ABD_VARS)
frp[["sample_id", "id", "exam_date", "us_fatty", "us_fatty_degree", "us_hepatic_other",
     "us_gallstone", "us_kidney_cyst"]].to_csv(
    os.path.join(OUT, "sampling", "frames", "ABD_PRIMARY_frame.csv"), index=False, encoding="utf-8-sig")

# ================= 域④ abdominal ultrasound (hospital) =================
rl("\n—— 域④ abdominal ultrasound（hospital）——")
us = pd.read_csv(r"STUDY_ROOT/study-data-root/data/processed/hospital_ultrasound_text_long.csv",
                 encoding="utf-8-sig", dtype=str)
us["text"] = (us["us_text"].fillna("") + " " + us["main_text"].fillna("")).str.strip()
frh = us[(us["text"] != "")].copy()
frh["_key"] = frh["id"].fillna("").str.strip() + "|" + frh["year"].fillna("").str.strip()
n0 = len(frh)
frh = frh[~frh["_key"].isin(excl_abdh)]
rl(f"框：hospital 腹超全框 {n0} − gold 300 = {len(frh)}（年分布：{frh['year'].value_counts().sort_index().to_dict()}）")
flags = pd.DataFrame([extract_abd(norm(u), m) for u, m in
                      zip(frh["us_text"].fillna(""), frh["main_text"].fillna(""))])
frh = pd.concat([frh.reset_index(drop=True), flags.reset_index(drop=True)], axis=1)
for c in ["us_fatty", "us_hepatic_other", "us_gallstone", "us_kidney_cyst"]:
    frh[c] = pd.to_numeric(frh[c], errors="coerce").fillna(0).astype(int)
bd = frh.apply(lambda r: abd_boundary(r["us_text"], r["main_text"], r)[0], axis=1)
rl(f"边界富集池：{int(bd.sum())} / {len(frh)}")
frh["sample_id"] = ""
stratum = {}
bp = frh[bd.values]
p_idx = bp.sample(n=N_PILOT, random_state=rng).index
frh.loc[p_idx, "sample_id"] = [f"ABD_HOSPITAL-P{i+1:02d}" for i in range(N_PILOT)]
for i, ix in enumerate(p_idx):
    stratum[f"ABD_HOSPITAL-P{i+1:02d}"] = "pilot"
rest_b = frh[(frh["sample_id"] == "") & bd.values]
d_idx = rest_b.sample(n=N_DECISION, random_state=rng).index
frh.loc[d_idx, "sample_id"] = [f"ABD_HOSPITAL-{i+1:03d}" for i in range(N_DECISION)]
for i, ix in enumerate(d_idx):
    stratum[f"ABD_HOSPITAL-{i+1:03d}"] = "decision"
rl(f"pilot=20 decision=100")
elig = frh[frh["sample_id"] == ""].copy()
elig["us_fatty_degree"] = elig["us_fatty_degree"].fillna("")
abn, nor = abd_anchors(elig, "ABD_HOSPITAL")
for i, (_, r) in enumerate(abn.iterrows()):
    frh.loc[r.name, "sample_id"] = f"ABD_HOSPITAL-AB{i+1:02d}"
    stratum[f"ABD_HOSPITAL-AB{i+1:02d}"] = "anchor_abnormal"
for i, (_, r) in enumerate(nor.iterrows()):
    frh.loc[r.name, "sample_id"] = f"ABD_HOSPITAL-AN{i+1:02d}"
    stratum[f"ABD_HOSPITAL-AN{i+1:02d}"] = "anchor_normal"
c_pool = frh[(frh["sample_id"] == "") & (~bd)]
yal = alloc(c_pool.groupby("year").size(), N_CONTROL)
c_n = 0
for y, k in yal.items():
    pool = c_pool[c_pool["year"] == y]
    take = pool.sample(n=int(k), random_state=rng).index
    for ix in take:
        c_n += 1
        frh.loc[ix, "sample_id"] = f"ABD_HOSPITAL-C{c_n:02d}"
        stratum[f"ABD_HOSPITAL-C{c_n:02d}"] = "control"
sel = frh[frh["sample_id"] != ""].copy()
sel["_yord"] = sel["year"]
rl(f"ABD_HOSPITAL 抽中合计：{len(sel)}（层分布：{pd.Series(stratum).value_counts().to_dict()}）")
sel, stratum, idmap = neutralize("ABD_HOSPITAL", sel, stratum)
frh["sample_id"] = frh["sample_id"].map(lambda v: idmap.get(v, v))
register(sel, "ABD_HOSPITAL", stratum)
selected_texts += sel["text"].tolist()
text_hashes += [{"domain": "ABD_HOSPITAL", "sample_id": r["sample_id"], "text_sha16": tsha(r["text"])}
                for _, r in sel.iterrows()]
ABD_HOSPITAL_VARS = ABD_VARS + ["main_discrepant"]
build_workbooks("ABD_HOSPITAL", sel, ABD_HOSPITAL_VARS)
frh[["sample_id", "id", "year", "us_fatty", "us_fatty_degree", "us_hepatic_other",
     "us_gallstone", "us_kidney_cyst"]].to_csv(
    os.path.join(OUT, "sampling", "frames", "ABD_HOSPITAL_frame.csv"), index=False, encoding="utf-8-sig")

# ================= 汇总产出 =================
os.makedirs(os.path.join(OUT, "sampling"), exist_ok=True)
link = pd.DataFrame(link_rows)
assert not link["sample_id"].duplicated().any(), "sample_id 重复"
link.to_csv(os.path.join(OUT, "sampling", "external_site_linkage_key.csv"), index=False, encoding="utf-8-sig")
pd.DataFrame(text_hashes).to_csv(os.path.join(OUT, "sampling", "workbook_text_hashes.csv"),
                                 index=False, encoding="utf-8-sig")

# PII 扫描（四域抽中文本；平台 10 类口径常用子集，与研究B脚本一致）
pii_patterns = {
    "手机号": r"\b1[3-9]\d{9}\b",
    "身份证18": r"\b\d{6}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b",
    "座机区号": r"\b0\d{2,3}-\d{7,8}\b",
    "住院/门诊号": r"(住院|门诊|病历|档案)号[:：]?\s*[A-Za-z0-9\-]{6,}",
    "姓名提示": r"(患者|病人|受检者)[姓名叫：:]{1,3}\S{2,3}",
}
pii_hits = {k: 0 for k in pii_patterns}
for txt in selected_texts:
    for name, pat in pii_patterns.items():
        if re.search(pat, str(txt)):
            pii_hits[name] += 1
rl(f"PII 扫描（抽中 {len(selected_texts)} 份）：" + "、".join(f"{k}={v}" for k, v in pii_hits.items()))

rl("\n—— 抽样汇总 ——")
rl(f"seed(sampling)={SEED_SAMPLE}  seed(bootstrap,登记备用)={SEED_BOOTSTRAP}")
rl(f"冻结管线 main.py SHA256：{sha256(os.path.join(FROZEN_CODE, 'main.py'))}")
rl(f"排除：gold 1,470 + trial170（stage2_linkage）+ trial160（adjudication_160_linkage）")
for lbl, p in [("external_site_linkage_key", os.path.join(OUT, "sampling", "external_site_linkage_key.csv")),
               ("text_hashes", os.path.join(OUT, "sampling", "workbook_text_hashes.csv")),
               ("frame_ECG", os.path.join(OUT, "sampling", "frames", "ECG_frame.csv")),
               ("frame_ECHO", os.path.join(OUT, "sampling", "frames", "ECHO_frame.csv")),
               ("frame_ABD_PRIMARY", os.path.join(OUT, "sampling", "frames", "ABD_PRIMARY_frame.csv")),
               ("frame_ABD_HOSPITAL", os.path.join(OUT, "sampling", "frames", "ABD_HOSPITAL_frame.csv"))]:
    rl(f"SHA256 {lbl}: {sha256(p)}  ({os.path.basename(p)})")
wd = os.path.join(OUT, "01-blind-annotation")
for dom in ("ECG", "ECHO", "ABD_PRIMARY", "ABD_HOSPITAL"):
    for suf in ("to_annotate.csv", "pilot20.csv"):
        p = os.path.join(wd, f"DA_{dom}_{suf}")
        if os.path.exists(p):
            rl(f"SHA256 DA_{dom}_{suf}: {sha256(p)}")

with open(os.path.join(OUT, "sampling", "four_domain_sampling_summary.txt"), "w",
          encoding="utf-8") as f:
    f.write("\n".join(rep) + "\n")
rl("\nDONE → sampling/four_domain_sampling_summary.txt")
