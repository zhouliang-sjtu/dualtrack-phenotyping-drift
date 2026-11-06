# -*- coding: utf-8 -*-
"""external site 外验 κ 的唯一文本聚类 bootstrap。

背景：600 条外验记录中同一份报告文本被多名就诊者复用（ECG 300 条仅 95 份唯一文本，
腹部超声 300 条仅 143 份唯一文本）。原分析脚本的 bootstrap 以
**记录（人）** 为重抽单位，低估了 κ 的方差。本脚本把**唯一文本（text_sha256）**作为
聚簇单位重抽（整簇抽取：抽中即带入该文本的全部记录），并同时给出记录级重抽口径与
设计效应，用于主文与附录的区间更新。

口径与主分析一致：explicit 三分类（0 不可判读 / 1 正常 / 2 异常），正类=2；
ESG/ABD 冻结聚合规则同 `outcome_explicit`；LLM 轨零重试（单字输入无解析输出者剔除）。
B=1000，seed=20261015（与主分析同种子）。
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r'study-data-root') / 'data' / 'external_site'
PANEL = ROOT / 'adjudication_dataset.xlsx'
CORPUS = ROOT / 'analysis_corpus.csv'
BATCH = ROOT
DICT_F = {'ECG': BATCH / 'external_site_ecg_dictionary.csv',
          'ABD': BATCH / 'external_site_abdomen_dictionary.csv'}
LLM_F = {'ECG': BATCH / 'external_site_llm_ecg.csv',
         'ABD': BATCH / 'external_site_llm_abdomen.csv'}
OUT = ROOT / 'external_site_text_clustered_kappa.csv'

B_BOOT = 1000
SEED = 20261015

ECG_ABN = ['ecg_af', 'ecg_pac_pvc', 'ecg_stt', 'ecg_avblock', 'ecg_bbb',
           'ecg_rate', 'ecg_srirr', 'ecg_axis', 'ecg_qwave_mi', 'ecg_other']
ECG_FLAGS = ['ecg_normal'] + ECG_ABN + ['ecg_unreadable']
ABD_FLAGS = ['us_fatty', 'us_fatty_degree', 'us_hepatic_other', 'us_gallstone',
             'us_kidney_cyst', 'us_unreadable']
DEG_MAP = {'轻': '轻度', '中': '中度', '重': '重度', '轻度': '轻度', '中度': '中度', '重度': '重度'}


def s(v):
    return '' if v is None or (isinstance(v, float) and math.isnan(v)) else str(v).strip()


def as_int(v, default=0):
    t = s(v)
    if t == '' or t.lower() == 'nan':
        return default
    try:
        return int(float(t))
    except Exception:
        return default


def kappa(pred, gold):
    n = len(pred)
    if n == 0:
        return float('nan')
    po = sum(1 for a, b in zip(pred, gold) if a == b) / n
    cats = set(pred) | set(gold)
    pe = sum((pred.count(c) / n) * (gold.count(c) / n) for c in cats)
    if pe == 1:
        return float('nan')
    return (po - pe) / (1 - pe)


def llm_flags(domain, raw):
    t = (raw or '').strip()
    a, b = t.find('{'), t.rfind('}')
    if a == -1 or b == -1:
        return None
    try:
        j = json.loads(t[a:b + 1])
    except Exception:
        return None
    if domain == 'ECG':
        return {k: ('1' if as_int(j.get(k, 0)) == 1 else '0') for k in ECG_FLAGS}
    deg = s(j.get('us_fatty_degree', ''))
    return {'us_fatty': '1' if as_int(j.get('us_fatty', 0)) == 1 else '0',
            'us_fatty_degree': DEG_MAP.get(deg, deg),
            'us_hepatic_other': '1' if as_int(j.get('us_hepatic_other', 0)) == 1 else '0',
            'us_gallstone': '1' if as_int(j.get('us_gallstone', 0)) == 1 else '0',
            'us_kidney_cyst': '1' if as_int(j.get('us_kidney_cyst', 0)) == 1 else '0',
            'us_unreadable': '1' if as_int(j.get('us_unreadable', 0)) == 1 else '0',
            'us_stone_strict': '1' if as_int(j.get('us_stone_strict', 0)) == 1 else '0',
            'us_post_chole': '1' if as_int(j.get('us_post_chole', 0)) == 1 else '0',
            'us_focal_liver': '1' if as_int(j.get('us_focal_liver', 0)) == 1 else '0'}


def outcome_explicit(domain, f):
    if f is None:
        return None
    if domain == 'ECG':
        if f.get('ecg_unreadable') == '1':
            return '0'
        return '2' if any(f.get(k) == '1' for k in ECG_ABN) else '1'
    if f.get('us_unreadable') == '1':
        return '0'
    if (f.get('us_stone_strict') == '1' or f.get('us_post_chole') == '1'
            or f.get('us_focal_liver') == '1' or f.get('us_fatty') == '1'):
        return '2'
    return '1'


def read_panel(domain):
    df = pd.read_excel(PANEL, sheet_name=domain)
    df['sample_id'] = df['sample_id'].astype(str).str.strip()
    return {r['sample_id']: s(r['outcome']) for _, r in df.iterrows()}


def read_csv_map(path):
    df = pd.read_csv(path, encoding='utf-8-sig', dtype=str).fillna('')
    return {r['sample_id'].strip(): r for _, r in df.iterrows()}


def ci(arr):
    a = np.array([x for x in arr if not math.isnan(x)], dtype=float)
    if len(a) < 50:
        return float('nan'), float('nan')
    return tuple(np.percentile(a, [2.5, 97.5]).round(4))


def se_from_ci(lo, hi):
    return (hi - lo) / (2 * 1.959963984540054)


rng = np.random.default_rng(SEED)
corpus = pd.read_csv(CORPUS, encoding='utf-8-sig', dtype=str).fillna('')
meta = {r['sample_id']: r['text_sha256'] for _, r in corpus.iterrows()}

rows = []
detail = []
for dom in ('ECG', 'ABD'):
    gold_map = read_panel(dom)
    dct = read_csv_map(DICT_F[dom])
    llmf = read_csv_map(LLM_F[dom])
    recs = []
    for sid in sorted(gold_map):
        g = gold_map[sid]
        cluster = meta.get(sid, '')
        dr = dct.get(sid)
        dict_flags = ({k: dr.get(k, '') for k in (ECG_FLAGS if dom == 'ECG' else ABD_FLAGS)}
                      if dr is not None else None)
        lr = llmf.get(sid)
        lf = llm_flags(dom, lr.get('llm_raw', '')) if lr is not None else None
        recs.append({'sid': sid, 'cluster': cluster, 'gold': g,
                     'dict': outcome_explicit(dom, dict_flags),
                     'llm': outcome_explicit(dom, lf)})
    for track in ('dict', 'llm'):
        sub = [r for r in recs if r[track] is not None]
        pred = [r[track] for r in sub]
        gold = [r['gold'] for r in sub]
        k = kappa(pred, gold)
        clusters = sorted({r['cluster'] for r in sub})
        idx_by_cluster = {c: [i for i, r in enumerate(sub) if r['cluster'] == c] for c in clusters}
        # ① 唯一文本聚类重抽
        k_boot = []
        for _ in range(B_BOOT):
            pick = rng.integers(0, len(clusters), len(clusters))
            idx = [i for j in pick for i in idx_by_cluster[clusters[j]]]
            k_boot.append(kappa([pred[i] for i in idx], [gold[i] for i in idx]))
        # ② 记录级重抽（复核旧口径）
        k_rec = []
        n = len(pred)
        for _ in range(B_BOOT):
            pick = rng.integers(0, n, n)
            k_rec.append(kappa([pred[i] for i in pick], [gold[i] for i in pick]))
        lo, hi = ci(k_boot)
        rlo, rhi = ci(k_rec)
        # ③ 唯一文本单条口径（每份唯一文本取首条记录）——有效样本量敏感性
        seen, pred_u, gold_u = set(), [], []
        for r in sub:
            if r['cluster'] in seen:
                continue
            seen.add(r['cluster'])
            pred_u.append(r[track])
            gold_u.append(r['gold'])
        rows.append({'domain': dom, 'track': track, 'n_records': len(sub),
                     'n_unique_texts': len(clusters), 'redundancy': round(len(sub) / len(clusters), 3),
                     'kappa': round(k, 4), 'ci_low': lo, 'ci_high': hi,
                     'ci_record_low': rlo, 'ci_record_high': rhi,
                     'se_cluster': round(se_from_ci(lo, hi), 4),
                     'se_record': round(se_from_ci(rlo, rhi), 4),
                     'design_effect': round(se_from_ci(lo, hi) / se_from_ci(rlo, rhi), 3),
                     'kappa_unique_text': round(kappa(pred_u, gold_u), 4),
                     'n_unique_eval': len(pred_u)})

out = pd.DataFrame(rows)
out.to_csv(OUT, index=False, encoding='utf-8-sig')
print(out.to_string(index=False))
print(f'\nwrote {OUT}')
