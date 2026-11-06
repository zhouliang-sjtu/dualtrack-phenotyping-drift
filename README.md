# dualtrack-phenotyping-drift

Data-governance and statistical-analysis materials for the study *Documentation-and-definition drift in AI-based clinical phenotyping and longitudinal health evidence: a seven-year cohort study*.

This repository is the public companion to the manuscript. It contains the reference-standard labels, the adjudication data set and decision tables, the frozen extractor and dictionary fingerprints, the annotation manuals and prompts, and the analysis code and result tables needed to check the reported statistics.

## Identifiers

| Resource | Identifier |
|---|---|
| This repository | https://github.com/zhouliang-sjtu/dualtrack-phenotyping-drift |
| Archived release (concept DOI) | 10.5281/zenodo.22694064 |
| OSF registration, study A (internal cohort) | 10.17605/OSF.IO/KUMVE (component HGBN9) |
| OSF registration, study B (external validation) | 10.17605/OSF.IO/6SKJE |
| Preregistration amendment | 10.17605/OSF.IO/Y4KH6 |

The GitHub repository is the canonical location for the code and result tables. The same release is archived on Zenodo under the concept DOI, which resolves to the most recent version. The reference-standard label table, adjudication tables, manuals and prompts are deposited on OSF as described in the Data sharing statement.

## What is not deposited

- The source cohort database and the annual community health-checkup extracts are not redistributed, because they contain person-level clinical records.
- Narrative text (the free-text ECG, echocardiography and abdominal-ultrasound reports) is not redistributed for the same reason. Every deposited record table carries record identifiers and labels only.
- The manuscript, figures, supplementary appendix, protocol and statistical analysis plan are submitted through the journal and are not duplicated here.

## Repository layout

```
data/gold-standard/     reference-standard labels (1,470 records, dual annotation + arbitration)
data/adjudication/      160-record adjudication data set and arbitration decision tables
data/manifests/         frozen extractor manifest, database freeze record, dictionary and rule-layer hashes
docs/manuals/           annotation manual v3.1, external-site appendix, v4.0 (PDF)
docs/prompts/           frozen structured-output prompts
docs/sampling/          sampling design note
docs/data-dictionary.md English glossary of result-table columns and of the annotation codes
code/                   analysis code (extraction, sampling, QC, adjudication, statistics, external validation)
results/                result tables underlying the reported estimates
results/external-site/  external-validation performance, agreement and repeatability tables
```

## Reference standard

`data/gold-standard/gold_standard_labels.csv` has one row per annotated record (570 ECG, 300 echocardiography, 300 abdominal ultrasound from each of two sites; 1,470 in total). Columns are the domain, the record identifier, the calendar year, the full label set of annotator A1, the full label set of annotator A2, a disagreement flag, an annotator note and the arbitration field. The note column records the clinical reason for the assigned label as written during annotation; the source tag of the annotator (A1 or A2) has been removed at export. Two physicians annotated every record independently and blinded to each other; disagreements were arbitrated and the decision is recorded.

`data/gold-standard/arbitration_record_round1.csv` lists the round-1 arbitration decisions with the ruled value and the codebook revision each decision triggered.

## Adjudication of the 2023 alarm

`data/adjudication/adjudication_dataset_160.csv` holds the 160 records drawn from the definition-divergence stratum and three anchor strata. It gives the rule prediction, both blinded clinician judgements, the agreement field, the final adjudicated panel outcome, the panel source, and the recorded reasons. The stratum composition and the 160-record panel reproduce the results reported in the manuscript (decision-residual stratum: 15 abnormal, 76 normal, 9 unreadable).

`data/adjudication/arbitration_decisions.csv` and `arbitration_flag_decisions.csv` hold the variable-level and flag-level arbitration decisions.

## Software and environment

The deterministic track is a Python dictionary and rule layer; the language-model track used Qwen2.5-7B, Qwen2.5-14B and GLM4-9B deployed locally through Ollama, with temperature 0, fixed seeds and versioned prompt fingerprints. Model, prompt version and prompt hash for every extractor are in `data/manifests/extractor_manifest.json`. Dictionary and rule-layer hashes are in `data/manifests/`.

Analysis code was run with CPython 3.13 and pandas 2.3.3, NumPy 2.5.4, SciPy 1.18.0, lifelines 0.30.3 and Matplotlib 3.11.1. No GPU is required to read or re-run the deposited statistics.

## Reproducing the reported statistics

Paths inside the scripts point to the study data root and must be redirected to a local copy of the deposited files; the source cohort itself is not part of this repository. Each script reads CSV or Excel inputs and writes CSV, TXT, NPY or PNG output; the block below gives the order in which the deposited tables are produced.

1. **Extraction and dictionary layer** — `code/extraction/` builds the frozen rule dictionaries and the text-mask layer, and documents the LLM extraction contract. Output: `data/manifests/dictionary_v2_freeze.txt` and the flag tables.
2. **Sampling** — `code/sampling/` draws the four reference-standard domains (`four_domain_sampling.py`, `sample_ecg_reference_standard.py`, `sample_abdomen_reference_standard.py`) and the external-validation sample (`external_site_sampling.py`). Output: `data/gold-standard/gold_standard_labels.csv` and the external-site sampling tables.
3. **Adjudication** — `code/adjudication/` builds the arbitration queue and workbook (`arbitration_queue.py`, `build_arbitration_workbook.py`), merges decisions (`merge_arbitration.py`) and prepares the relabelling workbook. Output: `data/adjudication/`.
4. **Quality control** — `code/qc/` verifies the returned annotation material (`returned_material_verification.py`), the repeatability analysis (`round2_repeatability.py`), the ECG acceptance panel (`model_acceptance_ecg.py`) and the numerical audit (`number_audit.py`). Output: `results/analysis/number_audit.csv`, `results/analysis/pii_scan_summary.csv`.
5. **Primary analysis** — `code/wp1/` runs the phenotype performance tables (`a1_phenotype_performance.py`), absolute burden (`a2_absolute_burden.py`), the locked Cox models (`a3_primary_analysis_lock.py`), operational burden (`a4_operational_burden.py`), the drift dose–response analysis (`a5_drift_dose_response.py`), the gate hierarchy (`a6_gate_hierarchy.py`), the divergence decomposition (`a7_divergent_decomposition.py`) and the exposure-timing sensitivity (`exposure_timing.py`). Output: `results/wp1/`.
6. **Version contrast and statistical support** — `code/wp1/version_contrast_run.py` (ΔHR for the v1/v3 phenotype definitions; inputs prepared by `make_version_contrast_inputs.py`), `code/analysis/` (agreement statistics, bootstrap intervals, definition-matched Cox models, specification curve, probabilistic quantitative bias analysis, SIMEX backfill, leave-2023-out sensitivity, synthetic differential replay, text-clustered standard errors, unadjusted sensitivity). Output: `results/analysis/`.
7. **External validation** — `code/external/` and `code/wp1/a1b_external_site_performance.py` compute the external-site transportability estimates and the text-clustered precision. Output: `results/external-site/`.

The mapping between each script, its input, and the deposited result table is listed in `docs/data-dictionary.md`. Agreement and transportability tables quoted in the manuscript are the files under `results/analysis/` and `results/external-site/`.

## Language policy

Code comments and result-table headers are partly in Chinese, the working language of the annotation team; this preserves the deployment wording of the clinical vocabulary and avoids retro-translation of label definitions. `docs/data-dictionary.md` gives the English meaning of every result-table column and of the annotation codes (domains, tracks, definition labels and stratum labels). Prompts and manuals are archived in their deployment language.

## Licences

Code: MIT (see `LICENSE`). Reference-standard labels, adjudication tables, manuals and prompts: CC BY-NC 4.0 (see `DATA-LICENSE.md`).

## Integrity

`RELEASE_SHA256.csv` lists the SHA-256 of every deposited file.
