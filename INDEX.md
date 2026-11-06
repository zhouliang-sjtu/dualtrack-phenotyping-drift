# File index and mapping to the manuscript

| Deposited file | Manuscript element |
|---|---|
| `data/gold-standard/gold_standard_labels.csv` | Data availability item 1: deidentified dual-annotation label table (1,470 records) |
| `data/gold-standard/arbitration_record_round1.csv` | Data availability item 3: arbitration decisions (round 1) |
| `data/adjudication/adjudication_dataset_160.csv` | Data availability item 2: 160-record adjudication data set; Summary, Findings; Figure 2; Table 3 |
| `data/adjudication/arbitration_decisions.csv` | Data availability item 3: variable-level arbitration decisions |
| `data/adjudication/arbitration_flag_decisions.csv` | Data availability item 3: flag-level arbitration decisions |
| `data/manifests/extractor_manifest.json` | Data availability item 4: extractor manifest (model, prompt hash, decoding settings, fingerprint) |
| `data/manifests/database_freeze_record.json` | Data availability item 4: database freeze record and fingerprints |
| `data/manifests/rule_layer_rhythm_normal_2023.sha256.txt` | Data availability item 4: rule-layer fingerprint |
| `data/manifests/dictionary_v2_freeze.txt` | Data availability item 5: abdomen dictionary freeze record |
| `docs/manuals/annotation_manual_v3_1.pdf` | Data availability item 7: annotation manual v3.1 |
| `docs/manuals/annotation_manual_v3_1_external_site_appendix.pdf` | Data availability item 7: external-site appendix |
| `docs/manuals/annotation_manual_v4_0.pdf` | Data availability item 7: annotation manual v4.0 |
| `docs/prompts/*.md` | Data availability item 6: frozen prompts (ECG, echocardiography, abdomen) |
| `docs/sampling/sampling_design.md` | Methods: reference-standard sampling |
| `docs/data-dictionary.md` | English glossary of result-table columns and annotation codes |
| `code/extraction/rule_dictionaries_and_layer.py` | Data availability item 5: ECG and echocardiography dictionaries and rule layer |
| `code/extraction/dictionary_abdomen_v2.py` | Data availability item 5: abdomen dictionary v2 |
| `results/agreement/*.csv` | Data availability item 8: 31 inter-rater agreement cells |
| `results/analysis/model_acceptance_*.csv` | Methods: prespecified acceptance and freeze rule |
| `results/analysis/drift_monitor_signals.csv` | Figure 3: eight-signal drift monitor |
| `results/analysis/definition_matched_agreement.csv` | Findings: definition-matched agreement |
| `results/analysis/specification_curve.csv` | Findings: specification-dependent significance |
| `results/external-site/*.csv` | Findings: external validation and text-clustered precision |
| `results/wp1/*.csv` | Findings and Tables 1-3: primary estimates, burden, gate hierarchy, divergence decomposition |

## External-site result tables

All files are in `results/external-site/`. The first sheet of the source workbook is `domain_performance_metrics.csv`; the remaining tables are the sheets that the source workbook stores separately.

| File | Content |
|---|---|
| `domain_performance_metrics.csv` | Per-domain, per-track, per-definition performance (sensitivity, specificity, PPV, NPV, F1, kappa and Wilson intervals) |
| `domain_performance_report.md` | Narrative report of the unblinded domain-level comparison, system output and negative findings |
| `domain_confusion_matrix_by_annotator.csv` | Confusion counts by domain, track, definition and annotator |
| `domain_performance_by_year.csv` | Performance stratified by calendar year and sampling stratum |
| `domain_flag_level_performance.csv` | Flag-level performance for every ECG and abdomen variable |
| `domain_unreadable_summary.csv` | Unreadable records and the identifiers involved, by domain and track |
| `domain_record_outcomes.csv` | Record-level outcomes: clinician, dictionary and LLM labels plus correctness indicators |
| `intra_rater_kappa_report.md` | Narrative report of the self-repeat (test-retest) intra-rater kappa analysis |
| `intra_rater_qc_checks.csv` | Eight-point completeness and integrity checks on the returned annotation material |
| `intra_rater_field_kappa.csv` | Field-level raw agreement, Cohen kappa and Gwet AC1 with reference thresholds |
| `intra_rater_annotator_summary.csv` | Annotator-level summary of the repeatability analysis |
| `intra_rater_relabel_basis.csv` | Record-level basis for each relabelled field |
