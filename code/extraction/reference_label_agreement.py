# -*- coding: utf-8 -*-
"""reference_label_agreement.py — reference-label concordance for the two quantitative
echocardiographic fields of the acceptance panel .

Why this file exists
--------------------
Table S3a accepts models against a reference label for ``reflux_grade`` (four-level ordinal).
The 31-cell inter-rater agreement table (Table S2b) covers the manual's *binary* annotation
cells only, so that table carries no row for ``reflux_grade`` or for the continuous
``ef_value``.  This script measures the A1-vs-A2 concordance of those two fields with the
same estimator that produced the 31 agreement cells (Cohen's kappa / Gwet's AC1 for the
ordinal field; exact numeric equality for the continuous field) so that the reference label
used in Table S3a has an explicit calibration record.

Input
-----
``--workbook``: the frozen annotation workbook (sheet ``ECHOCARDIOGRAPHY``, columns ``A1_<field>`` /
``A2_<field>``).  The workbook is **not** deposited in the release package because it
contains the clinical free-text reports; only this derived, text-free table is deposited.

Output
------
``results/reference_label_agreement.csv``

Usage
-----
    python reference_label_agreement.py --workbook <path to gold_standard_annotation_workbook_final.xlsx>
"""
import argparse
import os

import numpy as np
import pandas as pd

FIELDS = [('reflux_grade', 'ordinal_4_level'), ('ef_value', 'continuous')]


def clean(s):
    return s.astype(str).str.strip().replace({'': np.nan, 'nan': np.nan, 'None': np.nan})


def cohen_kappa(a, b):
    labels = sorted(set(a) | set(b))
    n = len(a)
    po = float(np.mean([x == y for x, y in zip(a, b)]))
    pe = sum((sum(1 for x in a if x == L) / n) * (sum(1 for y in b if y == L) / n)
             for L in labels)
    return ((po - pe) / (1 - pe)) if pe < 1 else 1.0, po


def gwet_ac1(a, b):
    labels = sorted(set(a) | set(b))
    n = len(a)
    po = float(np.mean([x == y for x, y in zip(a, b)]))
    pi = [(sum(1 for x in a if x == L) + sum(1 for y in b if y == L)) / (2 * n) for L in labels]
    pe = sum(p * (1 - p) for p in pi) / (len(labels) - 1) if len(labels) > 1 else 0.0
    return ((po - pe) / (1 - pe)) if pe < 1 else 1.0, po


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--workbook', required=True)
    ap.add_argument('--sheet', default='ECHOCARDIOGRAPHY')
    ap.add_argument('--out', default='')
    args = ap.parse_args()

    df = pd.read_excel(args.workbook, sheet_name=args.sheet, dtype=str)
    rows = []
    for field, kind in FIELDS:
        a, b = clean(df['A1_' + field]), clean(df['A2_' + field])
        d = pd.DataFrame({'a': a, 'b': b}).dropna()
        if kind == 'continuous':
            x = pd.to_numeric(d['a'], errors='coerce')
            y = pd.to_numeric(d['b'], errors='coerce')
            ok = (x.notna() & y.notna())
            d = d[ok]
            eq = int((x[ok] == y[ok]).sum())
            rows.append(dict(variable=field, type=kind, n_both=len(d), n_exact_equal=eq,
                             raw_agreement=round(eq / len(d), 3) if len(d) else '',
                             cohen_kappa='', gwet_ac1='',
                             a1_nonnull=int(a.notna().sum()), a2_nonnull=int(b.notna().sum()),
                             note='continuous field; exact numeric equality'))
        else:
            k, po = cohen_kappa(d['a'].tolist(), d['b'].tolist())
            ac1, _ = gwet_ac1(d['a'].tolist(), d['b'].tolist())
            rows.append(dict(variable=field, type=kind, n_both=len(d),
                             n_exact_equal=int((d['a'] == d['b']).sum()),
                             raw_agreement=round(po, 3), cohen_kappa=round(k, 3),
                             gwet_ac1=round(ac1, 3),
                             a1_nonnull=int(a.notna().sum()), a2_nonnull=int(b.notna().sum()),
                             note='four-level ordinal; concordant value is the consensus reference'))
    out = pd.DataFrame(rows, columns=['variable', 'type', 'n_both', 'n_exact_equal',
                                      'raw_agreement', 'cohen_kappa', 'gwet_ac1',
                                      'a1_nonnull', 'a2_nonnull', 'note'])
    p = args.out or os.path.join('results', 'reference_label_agreement.csv')
    out.to_csv(p, index=False, encoding='utf-8-sig')
    print(out.to_string(index=False))
    print('output ->', p)


if __name__ == '__main__':
    main()
