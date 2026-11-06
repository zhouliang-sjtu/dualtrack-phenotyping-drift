# -*- coding: utf-8 -*-
"""dictionary_abdomen_v2.py —— ABD 词典第二版（门控流程第二步：第一版骨架 + 最小增量）
增量清单（来自 Step 1 误差清单 + 抽查定性）：
  I1 弱化词段排除：含"稍增强/稍增粗/稍强/稍密集/稍粗"的句子不参与 fatty 双要素（V3.0-2）
  I2 否定语境修复："无明显占位效应"不计"占位"（否定优先规则）
  I3 描述式肝囊肿：肝内…(无回声|液性团块|囊性团块) → hepatic_other=1（H5）
  I4 息肉描述式：胆囊壁上中等/稍高回声向腔内凸出+无声影 → gallstone=1（G2）
  I5 结石描述式：胆囊/胆管段内强回声+声影/随体位移动（无声影否定）→ gallstone=1 & stone_strict（G3）
  I6 肝内强回声不入胆系（G1）
  I7 描述式肾囊肿：肾…无回声 → kidney_cyst=1（K1）
  I8 V3.0-1a：囊肿长径≥10mm → outcome=2（_cyst_large）
  I9 胆囊切除术后 → outcome=2
  输出额外内部字段供 outcome 聚合：_stone_strict/_cyst_large/_post_chole/_focal_liver
"""
import re

NEG_PRE = r"(未见|无明显|没有|无)\s*(明显)?\s*$"

def _split_segs(t):
    return [s for s in re.split(r"[。；；\n]", t) if s.strip()]

def _hit_with_neg(t, pattern):
    for m in re.finditer(pattern, t):
        pre = t[max(0, m.start() - 10):m.start()]
        if re.search(NEG_PRE, pre):
            continue
        return True
    return False

def _cyst_large(t):
    """V3.0-1a：囊肿长径≥10mm（尺寸在描述词后、前两个模式分别匹配）"""
    pats = [
        r"(肾|肝)[^。；\n]{0,16}(无回声|囊肿|液性团块|囊性团块)[^。；\n]{0,34}?(\d+(?:\.\d+)?)\s*[×xX\*/]\s*(\d+(?:\.\d+)?)\s*(cm|mm)?",
        r"(\d+(?:\.\d+)?)\s*[×xX\*/]\s*(\d+(?:\.\d+)?)\s*(cm|mm)?[^。；\n]{0,6}(无回声|囊肿|液性团块|囊性团块)",
    ]
    for pat in pats:
        for m in re.finditer(pat, t):
            if pat is pats[0]:
                a_, b_, unit = float(m.group(3)), float(m.group(4)), m.group(5) or 'mm'
            else:
                a_, b_, unit = float(m.group(1)), float(m.group(2)), m.group(3) or 'mm'
            scale = 10 if unit == 'cm' else 1
            if max(a_, b_) * scale >= 10:
                return 1
    return 0

def extract_abd_v2(t, site='primary', main_text=""):
    """分站词典第二版（per-site：manifest ABDOMINAL_ULTRASOUND_PRIMARY/ABDOMINAL_ULTRASOUND_HOSPITAL 本为两个 extractor）。
    site='primary'：other 含描述式囊肿（≥10mm，primary gold 0.920 证实）；site='hospital'：other 用窄词表（hospital gold 0.933 证实），
    描述式囊肿经内部字段 _cyst_large 只进 outcome（hospital site flag-outcome 分离惯例）。"""
    t = t or ""
    main_text = str(main_text or "")
    unreadable = 1 if (not t.strip() or re.search(r"^\s*[×xX弃检]*\s*$", t) or '免检' in t[:10]) else 0
    if unreadable:
        return {'us_fatty': 0, 'us_fatty_degree': '', 'us_hepatic_other': 0, 'us_gallstone': 0,
                'us_kidney_cyst': 0, 'us_unreadable': 1, '_stone_strict': 0, '_cyst_large': 0,
                '_post_chole': 0, '_focal_liver': 0, '_polyp': 0}
    # ---- I1 弱化词段排除（保留 v1 双要素：细密 AND (衰减|欠清)） ----
    segs = [s for s in _split_segs(t) if not re.search(r"稍(?:增强|增粗|强|密集|粗)", s)]
    t_eff = "。".join(segs)
    in_us = bool(re.search(r"脂肪肝", t))
    in_main = bool(re.search(r"脂肪肝", main_text))
    desc_hit = bool(re.search(r"细密", t_eff) and re.search(r"衰减|欠清", t_eff))
    fatty = 1 if (in_us or in_main or desc_hit) else 0
    m = re.search(r"脂肪肝[^。；\n]{0,8}?(轻度|中度|重度)|((轻度|中度|重度)[^。；\n]{0,6}?脂肪肝)", t + " " + main_text)
    deg = (m.group(1) or m.group(2) or "") if m else ("轻度" if fatty else "")
    # ---- I2 hepatic_other（描述式囊肿移出 flag（两站公约数），囊肿异常性归 outcome 层 V3.0-1a；
    #      补血管瘤样/钙化样描述式（primary gold H5 族），否定窗口保护） ----
    other = 0
    focal_liver = 0
    if re.search(r"血吸虫|血管瘤|肝硬化", t):
        other = 1
    if re.search(r"肝硬化|血吸虫", t):
        focal_liver = 1
    if _hit_with_neg(t, r"肝囊肿"):
        other = 1
    occ = False
    for m in re.finditer(r"占位", t):
        pre = t[max(0, m.start() - 12):m.start()]
        if re.search(NEG_PRE, pre) or re.search(r"无明显占位效应", t):
            continue
        occ = True
    if occ:
        other = 1
        focal_liver = 1
    # 描述式囊肿 flag（仅 primary-care site启用；hospital site经 _cyst_large 只进 outcome）
    if site == 'primary' and _cyst_large(t):
        other = 1
    # ---- I4/I5/I6 gallstone ----
    stone_strict = 0
    polyp = 0
    gallstone = 0
    if re.search(r"胆(囊|管)?(结石|息肉)", t):
        gallstone = 1
        if re.search(r"结石", t):
            stone_strict = 1
        else:
            polyp = 1
    gall_segs = [s for s in _split_segs(t) if re.search(r"胆囊|胆总管|胆管", s)]
    for seg in gall_segs:
        if '肝内' in seg.split('胆囊')[0].split('胆总管')[0].split('胆管')[0]:
            continue  # I6 肝内强回声不入胆系
        if re.search(r"(团状|点状|斑状)?强回声", seg) and \
                (re.search(r"声影", seg) or re.search(r"随体位[^。；\n]{0,8}移动", seg)) and \
                not re.search(r"无声影", seg):
            gallstone = 1
            stone_strict = 1
        elif re.search(r"壁上?可见?[^。；\n]{0,10}(中等|强)回声[^。；\n]{0,12}向[^。；\n]{0,4}腔内(凸出|突起)", seg) and \
                re.search(r"无声影", seg) and not re.search(r"稍高回声", seg):
            gallstone = 1
            polyp = 1
    # ---- I7 kidney_cyst ----
    kidney_cyst = 1 if (re.search(r"肾囊肿", t) or _hit_with_neg(t, r"肾[^。；\n]{0,10}无回声")) else 0
    # ---- I8 V3.0-1a ----
    cyst_large = _cyst_large(t)
    post_chole = 1 if re.search(r"胆囊(切除|术后)", t) else 0
    return {'us_fatty': fatty, 'us_fatty_degree': deg, 'us_hepatic_other': other, 'us_gallstone': gallstone,
            'us_kidney_cyst': kidney_cyst, 'us_unreadable': 0, '_stone_strict': stone_strict,
            '_cyst_large': cyst_large, '_post_chole': post_chole, '_focal_liver': focal_liver, '_polyp': polyp}

def outcome_from_flags(f, site):
    """V3.0-1a 分站 outcome 聚合（2026-09-26 批准）：
    hospital site（ABD_HOSPITAL）= any-abnormal（依据 hospital site 关键词句+panel 共认实践：任一 V2.0 flag 阳性→2）；
    primary-care site（ABD_PRIMARY）= V3.0-1 从严（依据 primary care 仲裁裁定：脂肪肝/结石/术后/占位→2；囊肿/息肉/结晶→1）。
    """
    if f['us_unreadable'] == 1:
        return '0'
    if site == 'hospital':
        if (f['us_fatty'] == 1 or f['us_hepatic_other'] == 1 or f['us_gallstone'] == 1 or
                f['us_kidney_cyst'] == 1 or f['_stone_strict'] == 1 or f['_post_chole'] == 1 or
                f['_focal_liver'] == 1 or f['_cyst_large'] == 1):
            return '2'
        return '1'
    # primary：V3.0-1 从严
    if f['_stone_strict'] or f['_post_chole'] or f['_focal_liver'] or f['us_fatty'] == 1:
        return '2'
    return '1'

def outcome_v2(t, site='primary', main_text=""):
    f = extract_abd_v2(t, main_text)
    return outcome_from_flags(f, site)
