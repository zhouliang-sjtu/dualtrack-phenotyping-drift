# External-site domain performance report

Domain-level performance after unblinded comparison. Generated 2026-10-26; the OSF registration update was disclosed before this comparison (https://osf.io/6skje/overview, 2026-10-26 21:17 +08:00).

## 1. Reference standard

`adjudication_dataset.xlsx`: independent blinded double annotation (300 per domain) followed by arbitration of all disagreements (ECG 11, abdomen 5). Outcome distribution: ECG 0 x 8 / 1 x 181 / 2 x 111; abdomen 0 x 5 / 1 x 157 / 2 x 138. The self-repeat intra-rater kappa gate passed 4/4 (ECG A1/A2 = 1.000/1.000; abdomen A1 = 1.000, A2 = 0.939).

## 2. System output (zero tuning after unblinding, frozen fingerprints)

- Dictionary track: ECG `code/extraction/rule_dictionaries_and_layer.py::extract_ecg` (stage-4 extension); abdomen `code/extraction/dictionary_abdomen_v2.py::extract_abd_v2(t, site='primary')`.
- Language-model track: Ollama qwen2.5:14b, temperature 0.0, seed 42; ECG prompt v1 sha16 = dbb1ebe717ad3497; abdomen prompt v2 sha16 = bcdc6563420538bb.
- Aggregation: ECG explicit = V3.0 explicit-positive (unreadable 1 to 0; any of the ten enumerated flags = 1 to 2; otherwise 1); abdomen explicit = dictionary v2 V3.0-1, strict per site (primary).
- Naive (ECG only, secondary endpoint): unreadable to 0; normal 1 to 1; any abnormal flag = 1 to 2.

## 3. Statistical specification (protocol v2.1 section 6)

Phenotype-level positive class = 2 (abnormal); sensitivity, specificity, PPV, NPV, F1 and kappa with bootstrap 95% CI (B = 1,000, SEED_BOOTSTRAP = 20261015, paired resampling clustered by person). Raw agreement is also reported with Wilson 95% CI, the wording used in the registration text. Flag level: raw agreement, Cohen kappa, Gwet AC1 (q = 2 for binary, 3 for three-class, 4 for fatty-liver grade; mandatory because the external-site text is highly repetitive), precision, recall, F1. H1 (per domain): explicit kappa >= 0.90 and CI lower bound > 0.85; failures are reported verbatim without post hoc exclusion. Each of the three ECG enumeration strata contains only one record: coverage is reported and no within-stratum kappa is inferred (see the year and stratum table).

## 4. Negative findings reported as observed (no retrospective correction)

1. System-detected unreadable records = 0. Clinicians marked 13 records unreadable (ECG 8, abdomen 5) with the text forms refusal / declined / abandoned / none / 999 / not done / not examined, none of which is in the frozen stage-4 unreadable lexicon (x, abandoned, refused, poor image quality, etc.); the language-model track is covered in the unreadable section. This result is reported as observed under the zero-tuning constraint and defines the documented limitation of the style transfer from the index site to the external site; no rule was added.
2. The corpus is highly repetitive: 600 records contain only 236 unique texts (ECG and abdomen combined), so flag-level kappa is inflated by repeated text and AC1 is mandatory.
3. Language-model track missing output: ECG 1, abdomen 0 (EXTECG-186); the model returned no parseable JSON (the instance text is the single character for "none"). Under the zero-tuning constraint there was no retry and no added prompt; the record is removed from the language-model denominator and recorded in the verification table, while the dictionary track is unaffected.

## 5. Output structure

Phenotype-level main endpoint / three-class confusion / year and stratum / flag level / unreadable section / record detail / verification.
