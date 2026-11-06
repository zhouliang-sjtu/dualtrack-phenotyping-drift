# -*- coding: utf-8 -*-
"""external_site_sampling.py —— external site（外部体检库）双域外部验证确认性抽样
（外部验证协议 v2.0 §4 + OSF Amendment 1 GUID y4kh6）

设计要点
--------
1) 双域独立抽样框：ECG（ecg_text）300 份、ABD（us_text）300 份；同一主种子域间独立派生。
2) 分层：年(2019/2020/2021) × 报告风格(枚举式=规范化文本含内联顿号"、"/叙述式)，
   共 6 层，按层规模比例分配（最大余数法，非空层至少 1）。
   实测：external site 的 ECG 文本极少含内联顿号，枚举式层年仅 853–2,302 份（占比 <1%），
   按"非空层至少 1"规则各仅分得 1 份；此为注册分层方案在 external site 文体下的固有退化，
   不改动注册的 年×风格 分层定义，仅在 summary 中如实登记层规模与分配。
3) 框在 wave 层建（wave_level.csv.gz，即 after the frozen text mask 的现行冻结层），
   叙事文本按 Amendment #9 从 raw_mirror 取**未截断全文**，主键 id 一致。
   镜像层未做 frozen text mask，故取全文时补做同一掩码 (?<![\\d.])\\d{7,}(?![\\d.]) → [REDACTED]，
   并以 mask(clean[:150]) == wave_v1.2_text 做强一致性断言（实测全库 0 例不可解析）。
   实测：external site 为体检结论式短文本，wave 层 ecg_text/us_text 中恰为 150 字符（截断上限）者
   分别仅 13 / 11 份（各占约 0.002%），故 Amendment #9 的"未截断全文"条款对 external site 近乎恒真；
   仍照条款实现，作为治理保全而非文本补全。
4) pilot 培训试标（20/域）**取消**：标注员/仲裁员已深度参与 L1 金标准、L2 四域两轮工作，
   对 V3.1 codebook 口径充分熟悉；改以《external site 附录 v0》承担口径校准职能。
   Amendment 1 §C 将 pilot-first calibration 列为 unchanged element，故此为注册偏离，
   须在 sampling summary 与 manuscript 的 Registration deviations 节披露（同 2026-09-25 先例）。
5) 盲法：乱序后赋中性编号 EXTECG-001..300 / EXTABD-001..300；
   年份、伪标识、层别一律不进标注员可见文件，仅存 sampling/external_site_linkage_key.csv。
6) 医生签名净化（2026-10-15 release 前修订，second de-identification pass after the frozen text mask）：external site 原始结论文本行尾残留
   检查医生签名（"----检查医生：X""——X""___X""-X""检查医生：X"五形态，实测两域 30 份 / 11 人），
   属医务人员个人信息且与"来源机构匿名"承诺冲突；在一致性断言（镜像 vs wave）通过之后、
   落盘之前按行尾签名模式移除，只删签名段、不动临床内容；净化份数登记于 summary，
   并以签名扫描命中=0 作为放行门（PII 模式自五项扩至六项）。

输出
----
  外部验证/sampling/external_site_sampling_frame_ecg.csv.gz   ECG 全框 + 层标记 + 抽中状态
  外部验证/sampling/external_site_sampling_frame_abdomen.csv.gz   ABD 全框
  外部验证/sampling/external_site_linkage_key.csv        600 份内部连接表（不随 release 发放）
  外部验证/sampling/external_site_sampling_summary.txt        层×抽样汇总 + SHA256 + PII 扫描
  dataset/03-external-validation-annotation/01-blind-annotation/EXTERNAL_ECG_to_annotate.csv    空白to_annotate包（A1/A2 分栏，与其他域同一 schema）
  dataset/03-external-validation-annotation/01-blind-annotation/EXTERNAL_ABD_to_annotate.csv
"""
import gzip
import hashlib
import os
import re
import sys

import numpy as np
import pandas as pd

ROOT = r"STUDY_ROOT"
EC = os.path.join(ROOT, "reference-data")
EV = os.path.join(EC, "外部验证")
SAMP = os.path.join(EV, "sampling")
BLIND = os.path.join(EC, "dataset", "03-external-validation-annotation", "01-blind-annotation")

PDD = r"STUDY_ROOT/study-data-root/data/external_site"
WAVE = os.path.join(PDD, "wave_level.csv.gz")
WAVE_SHA_EXPECT = "e82ca0a5e526f96906fe34aa02260213b5d1f03767dabfed81362686375cf8dc"
MIR = os.path.join(PDD, "raw_mirror", "external_{y}.csv.gz")

FROZEN_CODE = os.path.join(ROOT, "code")
AMEND_PDF = os.path.join(ROOT, "osf-preregistration", "03_external-validation",
                         "OSF_Amendment_1_StudyB_DualDomainExtension Submission.pdf")
AMEND_GUID = "y4kh6"
AMEND_SHA_EXPECT = "599dd44379f326688a4f4f84e858c1a8d90a2ad3caff5b2a650564a5d55442ac"

OSF_DOI = "10.17605/OSF.IO/6SKJE"
SEED_MAIN = 20261015          # Amendment 1 冻结（2026-09-30T14:41:25Z）之后生成
SEED_BOOTSTRAP = 20261015     # 预登记：bootstrap B=1000 重抽种子（按人聚类）
N_FORMAL = 300
N_PILOT = 0                   # 取消，见模块 docstring 第 4 条
YEARS = ["2019", "2020", "2021"]
MASK_PAT = r"(?<![\d.])\d{7,}(?![\d.])"   # 与 text_mask_v12.py 完全一致

ECG_VARS = ["ecg_normal", "ecg_af", "ecg_pac_pvc", "ecg_stt", "ecg_avblock", "ecg_bbb",
            "ecg_rate", "ecg_srirr", "ecg_axis", "ecg_qwave_mi", "ecg_other", "ecg_unreadable"]
ABD_VARS = ["us_fatty", "us_fatty_degree", "us_hepatic_other", "us_gallstone",
            "us_kidney_cyst", "us_unreadable"]

DOMAINS = [
    dict(key="ECG", prefix="EXTECG", seed=SEED_MAIN + 1, fname="EXTERNAL_ECG_to_annotate.csv",
         frame="external_site_sampling_frame_ecg.csv.gz",
         wave_col="ecg_text", mir_col="心电图结果", vars=ECG_VARS),
    dict(key="ABD", prefix="EXTABD", seed=SEED_MAIN + 2, fname="EXTERNAL_ABD_to_annotate.csv",
         frame="external_site_sampling_frame_abdomen.csv.gz",
         wave_col="us_text", mir_col="B超结果", vars=ABD_VARS),
]

sys.path.insert(0, FROZEN_CODE); sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # deposited frozen main.py (sampling/) takes precedence
from main import norm  # noqa: E402  与冻结管线同一规范化（零调参）

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


def sha16(t):
    return hashlib.sha256(str(t).encode("utf-8")).hexdigest()[:16]


def mask(t):
    """frozen text mask 同源掩码：7+ 位连续数字（前后非数字非小数点）→ [REDACTED]"""
    return re.sub(MASK_PAT, "[REDACTED]", t)


# 行尾检查医生签名（四种形态：横线/em-dash/下划线（1 个或多个）+ 可选"检查医生："标签 + 人名；
# 或裸"检查医生：人名"）。仅匹配整段文本末尾（无 re.M），签名恒在最后一行；
# 只删签名段，不动临床内容。{1,} 是为覆盖"-张国涛"式单连字符签名（实测 EXTABD-056），
# 行中数字区间（如"0.05-0.1mV"）因不在串尾且尾部含非中文字符而不会误匹配。
SIG_PAT = re.compile(
    r"(?:[-_—–―]{1,}\s*(?:检查医生|医师|医生)?\s*[:：]?\s*|(?:检查医生|医师|医生)\s*[:：]\s*)"
    r"[\u4e00-\u9fa5]{2,4}\s*$"
)


def strip_sig(t):
    """移除行尾检查医生签名段（2026-10-15 release 前修订，见 docstring 第 6 条）"""
    return SIG_PAT.sub("", t).rstrip()


# ---------- 执行门 1：ASSERT_OSF_DOI（external 确认性抽样须在 OSF 注册获得 DOI 之后执行） ----------
if not OSF_DOI.startswith("10."):
    raise SystemExit(
        "[ASSERT_OSF_DOI] external 确认性抽样必须在 OSF 注册获得 DOI 之后执行。\n"
        "  2026-09-21 的 n=520 初抽已定性为『工作量估算性预抽』and superseded，\n"
        "  stored in reference-data/。")

# ---------- 执行门 2：Amendment 1 冻结确认（时序纪律：fresh seed 须在 amendment 冻结后生成） ----------
if AMEND_GUID != "y4kh6":
    raise SystemExit("[ASSERT_AMENDMENT] Amendment 1 GUID 须为 y4kh6。")
if not os.path.exists(AMEND_PDF):
    raise SystemExit(f"[ASSERT_AMENDMENT] 缺 Amendment 1 提交件：{AMEND_PDF}")
_a = sha256(AMEND_PDF)
if _a != AMEND_SHA_EXPECT:
    raise SystemExit(
        f"[ASSERT_AMENDMENT] Amendment 1 提交件指纹不符（registered 2026-09-30T14:41:25Z）。\n"
        f"  期望 {AMEND_SHA_EXPECT}\n  实际 {_a}")

# ---------- 执行门 3：框源版本锁定（v1.2 = after the frozen text mask现行冻结层） ----------
if not os.path.exists(WAVE):
    raise SystemExit(f"[ASSERT_FRAME] 缺 wave 冻结层：{WAVE}")
_w = sha256(WAVE)
if _w != WAVE_SHA_EXPECT:
    raise SystemExit(f"[ASSERT_FRAME] wave_level 指纹不符。\n  期望 {WAVE_SHA_EXPECT}\n  实际 {_w}")

rl("=== external site 双域外部验证确认性抽样（协议 v2.0 §4 + Amendment 1 y4kh6）===")
rl(f"执行门：OSF DOI={OSF_DOI}；Amendment GUID={AMEND_GUID} 提交件 SHA256={_a}")
rl(f"框源：{WAVE}")
rl(f"      SHA256={_w}  size={os.path.getsize(WAVE):,} B")
rl(f"主种子 SEED_MAIN={SEED_MAIN}（域间独立派生：ECG={SEED_MAIN+1}，ABD={SEED_MAIN+2}）；"
   f"SEED_BOOTSTRAP={SEED_BOOTSTRAP}（预登记）")
rl(f"目标份数：每域 formal={N_FORMAL}，pilot={N_PILOT}（pilot 取消，见下方披露）")


# ---------- 分层比例分配（最大余数法，非空层至少 1）——沿用 2026-09-21 版实现 ----------
def alloc(strata_counts, n_total):
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


PII_PATTERNS = {
    "手机号": r"\b1[3-9]\d{9}\b",
    "身份证18": r"\b\d{6}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dXx]\b",
    "座机区号": r"\b0\d{2,3}-\d{7,8}\b",
    "住院/门诊号": r"(住院|门诊|病历|档案|流水|体检)号[:：]?\s*[A-Za-z0-9\-]{6,}",
    "姓名提示": r"(患者|病人|受检者)[姓名叫：:]{1,3}\S{2,3}",
    "医生签名": r"[-_—–―]{1,}\s*[\u4e00-\u9fa5]{2,4}\s*$|(?:检查医生|医师)\s*[:：]",
}

link_rows = []
products = []
os.makedirs(SAMP, exist_ok=True)
os.makedirs(BLIND, exist_ok=True)

for dom in DOMAINS:
    key, prefix = dom["key"], dom["prefix"]
    wc, mc = dom["wave_col"], dom["mir_col"]
    rl(f"\n{'='*66}\n【域 {key}】wave列={wc}  mirror列={mc}  seed={dom['seed']}\n{'='*66}")

    # ---- 1. 建框（wave 层）----
    d = pd.read_csv(WAVE, encoding="utf-8-sig", dtype=str,
                    usecols=["id", "year", wc], low_memory=False)
    rl(f"wave 全层行数：{len(d):,}")
    d = d[d["year"].isin(YEARS)].copy()
    rl(f"year∈{YEARS}：{len(d):,}")
    d["t"] = d[wc].fillna("").map(norm)
    d = d[d["t"] != ""].copy()
    d["style"] = np.where(d["t"].str.contains("、"), "枚举式", "叙述式")
    d["stratum"] = d["year"] + "|" + d["style"]
    rl(f"合格抽样框（norm 非空）：{len(d):,}")
    rl("层规模分布：")
    rl(d.groupby("stratum").size().to_string())
    _rl = d[wc].fillna("").str.len()
    rl(f"wave 层文本长度（字符）：median={int(_rl.median())} p95={int(_rl.quantile(.95))} "
       f"p99={int(_rl.quantile(.99))} max={_rl.max()}；"
       f"恰为 150（截断上限，疑似被截）={int((_rl == 150).sum()):,} 份"
       f"（占比 {(_rl == 150).mean()*100:.4f}%）")

    # ---- 2. 比例分配 + 层内无放回抽取 ----
    rng = np.random.default_rng(dom["seed"])
    d["selected"] = ""
    n_alloc = alloc(d.groupby("stratum").size(), N_FORMAL)
    for st, k in n_alloc.items():
        pool = d[(d["stratum"] == st) & (d["selected"] == "")]
        take = pool.sort_values("id", kind="mergesort").iloc[
            rng.choice(len(pool), int(k), replace=False)].index
        d.loc[take, "selected"] = "formal"
    assert (d["selected"] == "formal").sum() == N_FORMAL, "抽中份数不符"
    rl("层分配（最大余数法）：")
    rl(n_alloc.to_string())

    # ---- 3. 全框落盘（不含文本，仅 id/层/规模/状态）----
    frame = d[["id", "year", "style", "stratum", "selected"]].copy()
    frame["norm_len"] = d["t"].str.len().values
    frame["id"] = frame["id"] + "|" + frame["year"]      # record_key 形态，避免裸伪标识列
    frame = frame.rename(columns={"id": "record_key"})
    frame_path = os.path.join(SAMP, dom["frame"])
    # gzip mtime=0：确保重跑得到字节级一致的产物（SHA256 可复现）
    with gzip.GzipFile(frame_path, "wb", compresslevel=9, mtime=0) as gz:
        gz.write(frame.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig"))
    rl(f"全框落盘：{os.path.basename(frame_path)}  rows={len(frame):,}  "
       f"size={os.path.getsize(frame_path):,} B")

    # ---- 4. 从 raw_mirror 解析未截断全文（仅对抽中份）----
    sel = d[d["selected"] == "formal"].copy()
    sel["full_text"] = ""
    sel["mirror_date"] = ""
    sel["n_candidate"] = 0
    tiebreak_hits = 0
    for y in YEARS:
        sub = sel[sel["year"] == y]
        if len(sub) == 0:
            continue
        ids = set(sub["id"])
        m = pd.read_csv(MIR.format(y=y), encoding="utf-8-sig", dtype=str, low_memory=False,
                        usecols=["身份证号", "体检日期", mc])
        m = m.rename(columns={"身份证号": "id", mc: "raw"})
        m["id"] = m["id"].astype(str).str.strip().str.upper()
        m = m[m["id"].isin(ids)].copy()
        # G03 同源清洗：去 _x000D_（无 strip）→ 补 frozen text mask
        m["clean"] = m["raw"].fillna("").str.replace("_x000D_", "", regex=False)
        m["clean"] = m["clean"].map(lambda v: "" if str(v).lower() == "nan" else v)
        m["pred"] = [mask(c[:150]) for c in m["clean"]]
        m["_len"] = m["clean"].str.len()
        m["_ord"] = np.arange(len(m))
        tgt = sub[["id", wc]].rename(columns={wc: "wave_text"})
        j = tgt.merge(m[["id", "体检日期", "clean", "pred", "_len", "_ord"]],
                      on="id", how="left")
        j["ok"] = (j["pred"] == j["wave_text"]) & j["pred"].notna()
        jok = j[j["ok"]].copy()
        ncand = jok.groupby("id").size()
        # 确定性 tie-break：体检日期升序 → 全文长度降序 → 镜像原行序升序
        jok = jok.sort_values(["id", "体检日期", "_len", "_ord"],
                              ascending=[True, True, False, True],
                              kind="mergesort", na_position="last")
        pick = jok.drop_duplicates("id", keep="first")
        tiebreak_hits += int((ncand > 1).sum())
        mp_text = dict(zip(pick["id"], pick["clean"]))
        mp_date = dict(zip(pick["id"], pick["体检日期"].fillna("")))
        mp_n = ncand.to_dict()
        idx = sel.index[sel["year"] == y]
        sel.loc[idx, "full_text"] = [mask(mp_text.get(i, "")) for i in sel.loc[idx, "id"]]
        sel.loc[idx, "mirror_date"] = [mp_date.get(i, "") for i in sel.loc[idx, "id"]]
        sel.loc[idx, "n_candidate"] = [mp_n.get(i, 0) for i in sel.loc[idx, "id"]]
        del m, j, jok, pick
    n_unres = int((sel["full_text"].fillna("") == "").sum())
    rl(f"镜像全文解析：成功 {N_FORMAL - n_unres}/{N_FORMAL}，未解析 {n_unres}；"
       f"多候选需 tie-break 的份数 {tiebreak_hits}")
    if n_unres:
        raise SystemExit(f"[ASSERT_FULLTEXT] 域 {key} 有 {n_unres} 份无法从 raw_mirror 解析全文。")

    # 强一致性断言：掩码后前 150 字符必须与 wave v1.2 层文本逐字符相同
    pred = [mask(t[:150]) for t in sel["full_text"]]
    bad = int(sum(p != w for p, w in zip(pred, sel[wc].fillna(""))))
    assert bad == 0, f"[ASSERT_CONSISTENCY] 域 {key} 有 {bad} 份 mask(full[:150]) != wave_v1.2_text"
    rl(f"一致性断言 mask(full[:150]) == wave_v1.2_text：{N_FORMAL}/{N_FORMAL} 全部通过")

    # ---- 4.5 医生签名净化（second de-identification pass after the frozen text mask；只删签名段，不动临床内容）----
    n_sig = int(sel["full_text"].map(lambda t: bool(SIG_PAT.search(t))).sum())
    if n_sig:
        sig_ids = sel.loc[sel["full_text"].map(lambda t: bool(SIG_PAT.search(t))), "id"].tolist()
        sel["full_text"] = sel["full_text"].map(strip_sig)
        resid_sig = int(sel["full_text"].map(lambda t: bool(SIG_PAT.search(t))).sum())
        if resid_sig:
            raise SystemExit(f"[ASSERT_SIGNATURE] 域 {key} 净化后仍有 {resid_sig} 份行尾签名残留。")
        rl(f"签名净化：移除检查医生签名 {n_sig} 份（涉及 id：{', '.join(sig_ids[:6])}"
           f"{' …' if len(sig_ids) > 6 else ''}）；净化后复扫命中=0；"
           f"临床内容未改动（镜像 vs wave 一致性断言在净化前已通过）")

    sel["style_fulltext"] = np.where(sel["full_text"].str.contains("、"), "枚举式", "叙述式")
    n_flip = int((sel["style_fulltext"] != sel["style"]).sum())
    rl(f"风格判定：以 wave 层（截断 150）为准；全文重判后风格翻转 {n_flip} 份"
       f"（透明度指标，不改变层归属）")
    rl(f"全文长度：min={sel['full_text'].str.len().min()}  "
       f"median={int(sel['full_text'].str.len().median())}  "
       f"max={sel['full_text'].str.len().max()}  "
       f"（wave 层截断上限 150）")

    # ---- 5. 盲法重塑：乱序 + 中性编号（映射不落盘）----
    conf = sel.sample(frac=1.0, random_state=rng).copy()
    conf["sample_id"] = [f"{prefix}-{i+1:03d}" for i in range(len(conf))]
    assert conf["sample_id"].is_unique
    rl(f"盲法编号：{conf['sample_id'].iloc[0]} … {conf['sample_id'].iloc[-1]}"
       f"（乱序后顺序赋号，层别/年份/伪标识不进标注包）")

    # ---- 6. 空白to_annotate包（schema 与其他域一致：A1/A2 分栏同表）----
    annot_cols = []
    for a in ("A1", "A2"):
        annot_cols += [f"{a}_{v}" for v in dom["vars"]]
        annot_cols += [f"{a}_outcome", f"{a}_abnormal_basis",
                       f"{a}_uninterp_reason", f"{a}_note"]
    wb = pd.DataFrame({"sample_id": conf["sample_id"].values,
                       "text": conf["full_text"].values})
    for c in annot_cols:
        wb[c] = ""
    wb["arbitration"] = ""
    forbidden = {"year", "exam_date", "mirror_date", "pseudo_id", "id", "record_key",
                 "stratum", "style", "style_fulltext", "selected", "norm_len",
                 "n_candidate", "ef", "label", "ecg_text", "us_text"}
    assert not (forbidden & set(wb.columns)), f"盲法违例：{forbidden & set(wb.columns)}"
    wb_path = os.path.join(BLIND, dom["fname"])
    wb.to_csv(wb_path, index=False, encoding="utf-8-sig")
    rl(f"空白to_annotate包：{os.path.relpath(wb_path, EC)}  rows={len(wb)}  cols={len(wb.columns)}")

    # 文本多样性（external site 为体检结论式短文本，此项为 κ 可解释性的透明度指标）
    vc = conf["full_text"].value_counts()
    rl(f"标注包文本多样性：去重文本 {vc.size}/{len(conf)}；"
       f"最高频单文本占比 {vc.iloc[0]/len(conf)*100:.1f}%（“{vc.index[0][:20]}”）；"
       f"前 5 高频合计占比 {vc.head(5).sum()/len(conf)*100:.1f}%；"
       f"含内嵌换行（多脏器/多行结论拼接）{int(conf['full_text'].str.contains(chr(10)).sum())} 份")

    # ---- 7. PII 扫描（标注包全文）----
    texts = conf["full_text"].fillna("").tolist()
    hits = {n: sum(bool(re.search(p, t)) for t in texts) for n, p in PII_PATTERNS.items()}
    resid = sum(bool(re.search(MASK_PAT, t)) for t in texts)
    resid_loose = sum(bool(re.search(r"\d{7,}", t)) for t in texts)
    rl(f"PII 扫描（{len(texts)} 份全文）：" + "、".join(f"{k}={v}" for k, v in hits.items()))
    rl(f"掩码残留复核：MASK_PAT 命中={resid}（须为 0）；"
       f"宽松 \\d{{7,}} 命中={resid_loose}（含小数点邻接形态，信息项）")
    if resid:
        raise SystemExit(f"[ASSERT_PII] 域 {key} 掩码残留 {resid} 份。")
    if sum(hits.values()):
        rl("  ⚠ 上述 PII 模式命中非零，须人工复核后决定是否放行（不自动阻断）。")

    # ---- 8. 内部连接表行 ----
    for _, r in conf.iterrows():
        link_rows.append(dict(
            domain=key, sample_id=r["sample_id"], stratum=r["stratum"],
            record_key=f"{r['id']}|{r['year']}", year_or_date=r["year"],
            text_len=len(r["full_text"]), text_sha16=sha16(r["full_text"]),
            style_wave=r["style"], style_fulltext=r["style_fulltext"],
            mirror_date=r["mirror_date"], n_candidate=int(r["n_candidate"]),
            wave_norm_len=len(r["t"]), wave_text_sha16=sha16(r[wc]),
            seed=dom["seed"]))

    products += [(f"{key}_sampling_frame", frame_path), (f"{key}_blind_workbook", wb_path)]
    rl("层×抽中：")
    rl(conf.groupby("stratum").size().to_string())

# ---------- 内部连接表（blinding key，不随标注包发放）----------
link = pd.DataFrame(link_rows)
link_path = os.path.join(SAMP, "external_site_linkage_key.csv")
link.to_csv(link_path, index=False, encoding="utf-8-sig")
rl(f"\n内部连接表：{os.path.relpath(link_path, EC)}  rows={len(link)}")
rl(link.groupby(["domain", "stratum"]).size().to_string())
products.append(("external_site_linkage_key", link_path))

rl("\n—— 产物 SHA256 ——")
for label, p in products:
    rl(f"SHA256 {label}: {sha256(p)}  ({os.path.basename(p)}, {os.path.getsize(p):,} B)")

rl("\n—— pilot 取消披露（须同步至 manuscript 的 Registration deviations 节）——")
rl("Amendment 1（GUID y4kh6，registered 2026-09-30T14:41:25Z）§C『Unchanged elements』列有 "
   "pilot-first calibration（20/域，含每域≥3 例同类歧义即停规则）。")
rl("本次执行取消 pilot 培训试标：标注员与仲裁员已深度参与 L1 金标准（1,470）与 "
   "L2 四域定义对齐（560 + 自重复）两轮工作，对 V3.1 codebook 与三分类/outcome 口径充分熟悉。")
rl("替代性口径校准：随标注包提供的《external site 附录 v0》（最小化），仅就 external site 特异性口径作书面约定——"
   "external site 为纯所见文本（无主检字段，与 primary care site 同构）、ABD outcome 适用 V3.0-1a ABD_PRIMARY 从严口径、"
   "阴性所见留空惯例、note 列用法；不新增、不回改 V3.1 正文条款。")
rl("本偏离按预注册约定披露，性质同 2026-09-25 pilot 取消先例"
   "（见 dataset/02-四域定义对齐判读/sampling/four_domain_sampling_summary.txt）。")

with open(os.path.join(SAMP, "external_site_sampling_summary.txt"), "w", encoding="utf-8") as f:
    f.write("\n".join(rep) + "\n")
rl("\nDONE → 外部验证/sampling/external_site_sampling_summary.txt")
