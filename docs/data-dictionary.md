# Data dictionary

English meaning of every column of every deposited CSV table, and of the annotation codes used in the label tables. Chinese column names are retained in the external-site tables because they preserve the deployment wording of the clinical vocabulary; the meaning is given below.

## Annotation and analysis codes

| Code | Meaning |
|---|---|
| `ECG` | 12-lead electrocardiography narrative report |
| `ECHOCARDIOGRAPHY` | echocardiography narrative report |
| `ABDOMINAL_ULTRASOUND` | abdominal ultrasound narrative report |
| `ABDOMINAL_ULTRASOUND_HOSPITAL` | abdominal ultrasound from the hospital site |
| `ABDOMINAL_ULTRASOUND_PRIMARY` | abdominal ultrasound from the primary-care site |
| `A1 / A2` | the two clinicians who annotated every record independently and blinded |
| `naive` | rule that maps every enumerated abnormality to abnormal without an explicit-normal step |
| `explicit` | definition that requires an explicit positive statement for the abnormal class |
| `v1 / v3` | phenotype definition versions compared in the drift analysis |
| `class 0 / 1 / 2` | normal / indeterminate or unreadable / abnormal |
| `class A / N / U` | abnormal / normal / unreadable in the three-class tables |
| `kappa` | Cohen kappa, unweighted and nominal |
| `AC1` | Gwet first-order agreement coefficient |
| `H1` | prespecified primary agreement criterion |

## Primary analysis tables (results/wp1/)

### `results/wp1/absolute_burden_2023.csv`

| Column | Meaning |
|---|---|
| `item` | reported item |
| `value` | reported value |
| `unit` | unit of the reported value |
| `source` | source of the value (file, script or analysis step) |

### `results/wp1/definition_divergence_peryear.csv`

| Column | Meaning |
|---|---|
| `year` | calendar year |
| `n_texts` | number of narrative texts |
| `naive_abn_n` | number of records abnormal under the naive rule |
| `naive_abn_pct` | percentage abnormal under the naive rule |
| `explicit_abn_n` | number abnormal under the explicit definition |
| `explicit_abn_pct` | percentage abnormal under the explicit definition |
| `prevalence_shift_pp` | prevalence shift, in percentage points |
| `diverge_A1B0` | records abnormal under naive only |
| `diverge_A0B1` | records abnormal under the explicit definition only |
| `diverge_per_1000` | divergent records per 1,000 reports |

### `results/wp1/divergent_decomposition.csv`

| Column | Meaning |
|---|---|
| `stratum` | sampling or analysis stratum |
| `n_texts` | number of narrative texts |
| `naive_abn_n` | number of records abnormal under the naive rule |
| `explicit_abn_n` | number abnormal under the explicit definition |
| `divergent_n` | number of divergent records |
| `divergent_per_1000` | divergent records per 1,000 reports |
| `rule_layer_rhythm_n` | records normalised by the rhythm rule layer |
| `panel_pool_n` | records in the adjudication pool |

### `results/wp1/drift_alarm_ledger.csv`

| Column | Meaning |
|---|---|
| `year` | calendar year |
| `n_alarm_signals` | number of drift signals above threshold |
| `signal_family` | drift signal family |
| `strongest_z` | largest standardised deviation across signals |
| `detail` | signal detail |

### `results/wp1/drift_dose_response.csv`

| Column | Meaning |
|---|---|
| `dose_pct` | share of records replaced by 2023 drift material, in percent |
| `n` | number of records, pairs or observations analysed |
| `n_drift_2023` | number of 2023 drift records in the dose experiment |
| `naive_prev_pct` | naive prevalence, in percent |
| `explicit_prev_pct` | explicit-definition prevalence, in percent |
| `prev_distortion_pp` | prevalence distortion, in percentage points |
| `diverge_per_1000` | divergent records per 1,000 reports |
| `kappa_v1v3` | kappa between phenotype definition v1 and v3 |
| `n_alarm_signals` | number of drift signals above threshold |
| `alarm` | whether the drift monitor raised an alarm |
| `z_agreement` | standardised deviation of the agreement signal |
| `z_kappa` | standardised deviation of the kappa signal |
| `z_enum` | standardised deviation of the enumeration-style signal |

### `results/wp1/external_site_composite.csv`

| Column | Meaning |
|---|---|
| `domain` | clinical domain: ECG, ECHOCARDIOGRAPHY or ABDOMINAL_ULTRASOUND |
| `composite` | composite performance estimate |
| `n` | number of records, pairs or observations analysed |
| `kappa` | Cohen kappa |
| `kappa_lo` | lower 95% CI bound of kappa |
| `kappa_hi` | upper 95% CI bound of kappa |
| `sens` | sensitivity |
| `spec` | specificity (or model specification, where the column is named spec) |
| `ppv` | positive predictive value |
| `npv` | negative predictive value |
| `f1` | F1 score |

### `results/wp1/external_site_performance.csv`

| Column | Meaning |
|---|---|
| `domain` | clinical domain: ECG, ECHOCARDIOGRAPHY or ABDOMINAL_ULTRASOUND |
| `variable` | clinical variable or flag name |
| `kappa` | Cohen kappa |
| `kappa_lo` | lower 95% CI bound of kappa |
| `kappa_hi` | upper 95% CI bound of kappa |
| `sens` | sensitivity |
| `spec` | specificity (or model specification, where the column is named spec) |
| `ppv` | positive predictive value |
| `npv` | negative predictive value |
| `f1` | F1 score |
| `n` | number of records, pairs or observations analysed |
| `note` | free-text note |

### `results/wp1/gate_hierarchy.csv`

| Column | Meaning |
|---|---|
| `level` | gate level |
| `item` | gate item |
| `cohen_kappa` | Cohen kappa |
| `F1_pos` | F1 for the positive class |
| `gate` | prespecified acceptance gate |
| `fail_note` | reason a gate or check failed |
| `downstream_use` | downstream use of the variable |
| `kappa_3class` | three-class kappa |
| `sens_A` | sensitivity for class A (abnormal) |
| `spec_A` | specificity for class A |
| `kappa_lo` | lower 95% CI bound of kappa |
| `kappa_hi` | upper 95% CI bound of kappa |

### `results/wp1/operational_burden.csv`

| Column | Meaning |
|---|---|
| `metric` | metric name |
| `value` | reported value |
| `unit` | unit of the reported value |
| `source` | source of the value (file, script or analysis step) |

### `results/wp1/phenotype_performance.csv`

| Column | Meaning |
|---|---|
| `domain` | clinical domain: ECG, ECHOCARDIOGRAPHY or ABDOMINAL_ULTRASOUND |
| `definition` | phenotype definition version used for the label or the outcome |
| `scope` | analysis scope or subset |
| `n` | number of records, pairs or observations analysed |
| `kappa_3class` | three-class kappa |
| `raw_agreement` | raw agreement proportion |
| `sens_A` | sensitivity for class A (abnormal) |
| `spec_A` | specificity for class A |
| `ppv_A` | positive predictive value for class A |
| `npv_A` | negative predictive value for class A |
| `f1_A` | F1 for class A (abnormal) |
| `sens_N` | sensitivity for class N (normal) |
| `spec_N` | specificity for class N |
| `ppv_N` | positive predictive value for class N |
| `npv_N` | negative predictive value for class N |
| `f1_N` | F1 for class N (normal) |
| `sens_U` | sensitivity for class U (unreadable) |
| `spec_U` | specificity for class U |
| `ppv_U` | positive predictive value for class U |
| `npv_U` | negative predictive value for class U |
| `f1_U` | F1 for class U (unreadable) |
| `sens_A_lo` | lower 95% CI bound of sens_A |
| `sens_A_hi` | upper 95% CI bound of sens_A |
| `f1_A_lo` | lower 95% CI bound of f1_A |
| `f1_A_hi` | upper 95% CI bound of f1_A |
| `sens_N_lo` | lower 95% CI bound of sens_N |
| `sens_N_hi` | upper 95% CI bound of sens_N |
| `f1_N_lo` | lower 95% CI bound of f1_N |
| `f1_N_hi` | upper 95% CI bound of f1_N |
| `sens_U_lo` | lower 95% CI bound of sens_U |
| `sens_U_hi` | upper 95% CI bound of sens_U |
| `f1_U_lo` | lower 95% CI bound of f1_U |
| `f1_U_hi` | upper 95% CI bound of f1_U |
| `kappa_3class_lo` | lower 95% CI bound of kappa_3class |
| `kappa_3class_hi` | upper 95% CI bound of kappa_3class |

### `results/wp1/phenotype_performance_flag_level.csv`

| Column | Meaning |
|---|---|
| `domain` | clinical domain: ECG, ECHOCARDIOGRAPHY or ABDOMINAL_ULTRASOUND |
| `variable` | clinical variable or flag name |
| `scope` | analysis scope or subset |
| `n` | number of records, pairs or observations analysed |
| `tp` | true positives |
| `fp` | false positives |
| `fn` | false negatives |
| `tn` | true negatives |
| `gold_pos` | number positive in the reference standard |
| `ext_pos` | number positive by the extractor |
| `raw_agreement` | raw agreement proportion |
| `kappa` | Cohen kappa |
| `precision_1` | precision for class 1 |
| `recall_1` | recall for class 1 |
| `f1_1` | see the column name |

### `results/wp1/primary_analysis_estimates.csv`

| Column | Meaning |
|---|---|
| `role` | role of the estimate: primary, secondary or falsification control |
| `spec` | specificity (or model specification, where the column is named spec) |
| `claim` | estimate described in the manuscript |
| `claimed` | manuscript value |
| `actual_freeze` | value recomputed at the production freeze |
| `audit` | audit verdict |
| `note` | free-text note |

### `results/wp1/process_control_signals.csv`

| Column | Meaning |
|---|---|
| `site` | data source: index cohort or external site |
| `year` | calendar year |
| `n` | number of records, pairs or observations analysed |
| `median_len` | median narrative length, in characters |
| `inline_enum_pct` | percentage of texts with inline enumeration |
| `domain_mix_pct` | percentage of multi-domain texts |
| `ecg_prefix_pct` | percentage of texts with an ECG prefix |
| `note` | free-text note |

## Agreement and statistical-support tables (results/analysis/)

### `results/analysis/annotation_precision_projection.csv`

| Column | Meaning |
|---|---|
| `kappa_target` | target kappa used in the projection |
| `n_annotation` | number of annotated records |
| `corr_halfwidth_pct_of_HR` | half-width of the corrected interval as a percentage of the hazard ratio |
| `corr_lo` | lower bound of the corrected estimate interval |
| `corr_hi` | upper bound of the corrected estimate interval |

### `results/analysis/attendance_distribution.csv`

| Column | Meaning |
|---|---|
| `Waves attended` | number of examination waves attended |
| `Individuals` | number of individuals |
| `Person-year records` | number of person-year records |

### `results/analysis/attendance_sensitivity.csv`

| Column | Meaning |
|---|---|
| `Subset` | analysis subset |
| `Person-years` | number of person-years |
| `Events` | see the column name |
| `HR (95% CI)` | hazard ratio with 95% confidence interval |
| `p` | two-sided p value |

### `results/analysis/baseline_characteristics.csv`

| Column | Meaning |
|---|---|
| `Characteristic` | baseline characteristic |
| `n` | number of records, pairs or observations analysed |
| `Value` | reported value |

### `results/analysis/bootstrap_ci_extractors.csv`

| Column | Meaning |
|---|---|
| `domain` | clinical domain: ECG, ECHOCARDIOGRAPHY or ABDOMINAL_ULTRASOUND |
| `variable` | clinical variable or flag name |
| `model` | model name or version |
| `n` | number of records, pairs or observations analysed |
| `kappa` | Cohen kappa |
| `ci_lo` | lower bound of the 95% confidence interval |
| `ci_hi` | upper bound of the 95% confidence interval |
| `gate_f1` | prespecified F1 gate |

### `results/analysis/bootstrap_ci_peryear.csv`

| Column | Meaning |
|---|---|
| `extractor` | extractor (model or dictionary version) |
| `year` | calendar year |
| `n` | number of records, pairs or observations analysed |
| `kappa` | Cohen kappa |
| `ci_lo` | lower bound of the 95% confidence interval |
| `ci_hi` | upper bound of the 95% confidence interval |

### `results/analysis/cross_library_agreement.csv`

| Column | Meaning |
|---|---|
| `site` | data source: index cohort or external site |
| `year` | calendar year |
| `n` | number of records, pairs or observations analysed |
| `v3_pos_pct` | positive percentage under definition v3 |
| `v1_pos_pct` | positive percentage under definition v1 |
| `agreement_pct` | agreement percentage |
| `kappa` | Cohen kappa |

### `results/analysis/definition_matched_agreement.csv`

| Column | Meaning |
|---|---|
| `year` | calendar year |
| `n` | number of records, pairs or observations analysed |
| `v1_draft_pct` | positive percentage under the draft v1 definition |
| `v1_B_pct` | positive percentage under v1 variant B |
| `v1_A2_pct` | positive percentage under annotator A2 using v1 |
| `v3_A_pct` | positive percentage under v3 variant A |
| `v3_B_pct` | positive percentage under v3 variant B |
| `kappa_draft` | kappa under the draft definition |
| `agree_draft` | raw agreement under the draft definition |
| `kappa_matched` | kappa under the definition-matched comparison |
| `agree_matched` | raw agreement under the definition-matched comparison |
| `kappa_A2` | kappa between annotator A2 and the reference standard |
| `agree_A2` | raw agreement between annotator A2 and the reference standard |

### `results/analysis/definition_matched_cox.csv`

| Column | Meaning |
|---|---|
| `outcome_def` | outcome definition |
| `yearFE` | whether year fixed effects were included |
| `n_risk` | number at risk |
| `events` | number of events |
| `HR` | hazard ratio |
| `lo` | lower bound of the 95% confidence interval |
| `hi` | upper bound of the 95% confidence interval |
| `p` | two-sided p value |

### `results/analysis/dictionary_version_agreement.csv`

| Column | Meaning |
|---|---|
| `scope` | analysis scope or subset |
| `year` | calendar year |
| `n` | number of records, pairs or observations analysed |
| `pct_agree` | percentage agreement |
| `cohen_kappa` | Cohen kappa |
| `pct_v1_abn` | percentage abnormal under v1 |
| `pct_v3_abn` | percentage abnormal under v3 |

### `results/analysis/drift_monitor_signals.csv`

| Column | Meaning |
|---|---|
| `year` | calendar year |
| `agreement_pct` | agreement percentage |
| `kappa_v1v3` | kappa between phenotype definition v1 and v3 |
| `posrate_v1` | positive rate under definition v1 |
| `posrate_v3` | positive rate under definition v3 |
| `median_len` | median narrative length, in characters |
| `inline_enum_pct` | percentage of texts with inline enumeration |
| `domain_mix_pct` | percentage of multi-domain texts |
| `ecg_prefix_pct` | percentage of texts with an ECG prefix |
| `ngram_drift` | n-gram drift statistic |

### `results/analysis/e_value_table.csv`

| Column | Meaning |
|---|---|
| `spec` | specificity (or model specification, where the column is named spec) |
| `outcome` | outcome definition |
| `HR` | hazard ratio |
| `CI_lo` | lower bound of the 95% confidence interval |
| `CI_hi` | upper bound of the 95% confidence interval |
| `Evalue_point` | E-value for the point estimate |
| `Evalue_CI` | E-value for the confidence-interval bound |
| `Evalue_CI_crosses_1` | whether the E-value interval crosses 1 |

### `results/analysis/exposure_timing_sensitivity.csv`

| Column | Meaning |
|---|---|
| `spec` | specificity (or model specification, where the column is named spec) |
| `HR` | hazard ratio |
| `lo` | lower bound of the 95% confidence interval |
| `hi` | upper bound of the 95% confidence interval |
| `p` | two-sided p value |
| `n_risk` | number at risk |
| `n_events` | number of events |
| `exposure_note` | exposure definition used in the sensitivity analysis |

### `results/analysis/extraction_qc.csv`

| Column | Meaning |
|---|---|
| `model` | model name or version |
| `n` | number of records, pairs or observations analysed |
| `json_ok` | number of parseable JSON outputs |
| `json_rate` | share of parseable JSON outputs |
| `error` | error type or message |
| `bad_label` | number of outputs with an invalid label set |
| `bad_reflux` | number of outputs with an invalid reflux value |
| `bad_binary` | number of outputs with an invalid binary value |
| `bad_ef` | number of outputs with an invalid ejection fraction |

### `results/analysis/inference_latency_summary.csv`

| Column | Meaning |
|---|---|
| `model` | model name or version |
| `n` | number of records, pairs or observations analysed |
| `mean_latency_s` | mean inference latency, in seconds |
| `median_latency_s` | median inference latency, in seconds |
| `p95_latency_s` | 95th percentile inference latency, in seconds |
| `mean_completion_tokens` | mean number of completion tokens |
| `tokens_per_s` | generated tokens per second |
| `est_gpu_hours_per_1000` | estimated GPU hours per 1,000 reports |

### `results/analysis/intra_rater_self_repeat.csv`

| Column | Meaning |
|---|---|
| `domain` | clinical domain: ECG, ECHOCARDIOGRAPHY or ABDOMINAL_ULTRASOUND |
| `variable` | clinical variable or flag name |
| `rater` | annotator |
| `n` | number of records, pairs or observations analysed |
| `raw_agreement` | raw agreement proportion |
| `cohen_kappa` | Cohen kappa |
| `gwet_ac1` | Gwet AC1 agreement coefficient |
| `changed` | whether the label changed on repeat annotation |
| `v2_affected` | whether the record is affected by the v2 definition |

### `results/analysis/leave_2023_out_sensitivity.csv`

| Column | Meaning |
|---|---|
| `definition` | phenotype definition version used for the label or the outcome |
| `scope` | analysis scope or subset |
| `yearFE` | whether year fixed effects were included |
| `HR` | hazard ratio |
| `CI` | 95% confidence interval |
| `CIh` | upper bound of the 95% confidence interval |
| `p` | two-sided p value |

### `results/analysis/model_acceptance_ecg.csv`

| Column | Meaning |
|---|---|
| `model` | model name or version |
| `variable` | clinical variable or flag name |
| `n` | number of records, pairs or observations analysed |
| `raw_acc` | raw accuracy |
| `cohen_kappa` | Cohen kappa |
| `F1_pos` | F1 for the positive class |
| `acc@2018` | model accuracy in calendar year 2018 |
| `acc@2019` | model accuracy in calendar year 2019 |
| `acc@2020` | model accuracy in calendar year 2020 |
| `acc@2021` | model accuracy in calendar year 2021 |
| `acc@2022` | model accuracy in calendar year 2022 |
| `acc@2023` | model accuracy in calendar year 2023 |
| `acc@2024` | model accuracy in calendar year 2024 |
| `verdict` | verdict |
| `fail_note` | reason a gate or check failed |

### `results/analysis/model_acceptance_echocardiography.csv`

| Column | Meaning |
|---|---|
| `model` | model name or version |
| `variable` | clinical variable or flag name |
| `n` | number of records, pairs or observations analysed |
| `raw_acc` | raw accuracy |
| `cohen_kappa` | Cohen kappa |
| `F1_1` | F1 for class 1 |
| `acc@2023` | model accuracy in calendar year 2023 |
| `acc@2024` | model accuracy in calendar year 2024 |
| `acc@2025` | model accuracy in calendar year 2025 |
| `acc@2026` | model accuracy in calendar year 2026 |
| `verdict` | verdict |
| `fail_note` | reason a gate or check failed |
| `F1_0` | F1 for class 0 |
| `F1_none` | F1 for the none class |
| `F1_trace_mild` | F1 for the trace or mild class |
| `F1_moderate` | F1 for the moderate class |
| `F1_severe` | F1 for the severe class |

### `results/analysis/model_outputs_peryear.csv`

| Column | Meaning |
|---|---|
| `domain` | clinical domain: ECG, ECHOCARDIOGRAPHY or ABDOMINAL_ULTRASOUND |
| `outcome` | outcome definition |
| `extractor` | extractor (model or dictionary version) |
| `year` | calendar year |
| `n` | number of records, pairs or observations analysed |
| `cohen_kappa` | Cohen kappa |
| `F1_target` | F1 for the target class |

### `results/analysis/number_audit.csv`

| Column | Meaning |
|---|---|
| `id` | audit item identifier |
| `claim` | audit claim |
| `claimed` | claimed value |
| `actual` | recomputed value |
| `verdict` | audit verdict |

### `results/analysis/parameter_grid_check.csv`

| Column | Meaning |
|---|---|
| `HR_true` | assumed true hazard ratio |
| `kappa` | assumed kappa |
| `Se_eq_Sp` | whether sensitivity equals specificity |
| `HR_obs_analytic` | analytic observed hazard ratio |
| `HR_obs_sim_median` | median simulated observed hazard ratio |
| `rel_dev_pct` | relative deviation, in percent |
| `mc_se_logHR` | Monte Carlo standard error of log hazard ratio |
| `z` | see the column name |
| `verdict` | verdict |

### `results/analysis/participant_cascade.csv`

| Column | Meaning |
|---|---|
| `Step` | participant-flow step |
| `Records` | number of records |
| `Excluded` | number excluded |
| `Criterion` | exclusion criterion |

### `results/analysis/penalizer_sensitivity.csv`

| Column | Meaning |
|---|---|
| `spec` | specificity (or model specification, where the column is named spec) |
| `n_risk` | number at risk |
| `n_events` | number of events |
| `HR` | hazard ratio |
| `CI_lo` | lower bound of the 95% confidence interval |
| `CI_hi` | upper bound of the 95% confidence interval |
| `p` | two-sided p value |
| `penalizer` | ridge penaliser applied to the Cox model |

### `results/analysis/pii_scan_summary.csv`

| Column | Meaning |
|---|---|
| `source` | source of the value (file, script or analysis step) |
| `file` | file name |
| `rows` | number of rows |
| `mobile` | mobile number matches |
| `idcard18` | 18-digit identity-number matches |
| `idcard15` | 15-digit identity-number matches |
| `landline` | landline number matches |
| `email` | email address matches |
| `address` | address matches |
| `hometown` | hometown matches |
| `name_title` | name or title matches |
| `name_field` | name-field matches |
| `longnum` | long numeric string matches |

### `results/analysis/probabilistic_quantitative_bias.csv`

| Column | Meaning |
|---|---|
| `side` | direction of the bias analysis |
| `estimate` | bias-corrected estimate |
| `HR_observed` | observed hazard ratio |
| `HR_corrected` | bias-corrected hazard ratio |
| `corr_lo` | lower bound of the corrected estimate interval |
| `corr_hi` | upper bound of the corrected estimate interval |
| `attenuation_pct` | attenuation, in percent |
| `method` | correction method |

### `results/analysis/prompt_perturbation.csv`

| Column | Meaning |
|---|---|
| `variant` | prompt variant |
| `model` | model name or version |
| `variable` | clinical variable or flag name |
| `year` | calendar year |
| `n` | number of records, pairs or observations analysed |
| `kappa` | Cohen kappa |
| `F1_pos` | F1 for the positive class |
| `acc` | see the column name |
| `gate_pass` | whether the prespecified gate was met |

### `results/analysis/proxy_sensitivity_replay.csv`

| Column | Meaning |
|---|---|
| `rep` | replicate number |
| `HR_noFE` | hazard ratio without year fixed effects |
| `HR_yearFE` | hazard ratio with year fixed effects |
| `CI_lo_noFE` | lower 95% CI bound without year fixed effects |
| `CI_lo_yearFE` | lower 95% CI bound with year fixed effects |
| `CI_hi_noFE` | upper 95% CI bound without year fixed effects |
| `CI_hi_yearFE` | upper 95% CI bound with year fixed effects |
| `p_noFE` | p value without year fixed effects |
| `p_yearFE` | p value with year fixed effects |
| `draw` | replicate draw index |

### `results/analysis/proxy_sensitivity_summary.csv`

| Column | Meaning |
|---|---|
| `R` | number of replicates |
| `seed` | random seed |
| `HR_noFE_mean` | mean hazard ratio without year fixed effects across replicates |
| `HR_noFE_lo` | lower bound of the hazard ratio without year fixed effects |
| `HR_noFE_hi` | upper bound of the hazard ratio without year fixed effects |
| `HR_FE_mean` | mean hazard ratio with year fixed effects across replicates |
| `HR_FE_lo` | lower bound of the hazard ratio with year fixed effects |
| `HR_FE_hi` | upper bound of the hazard ratio with year fixed effects |
| `frac_noFE_significant` | fraction of replicates significant without year fixed effects |
| `frac_FE_p_above_005` | fraction of replicates with p above 0.05 with year fixed effects |

### `results/analysis/reference_error_attenuation.csv`

| Column | Meaning |
|---|---|
| `kappa_true` | assumed true kappa |
| `ref_error` | reference-standard error proportion |
| `kappa_measured` | measured kappa |
| `attenuation` | attenuation proportion |

### `results/analysis/reference_label_agreement.csv`

| Column | Meaning |
|---|---|
| `variable` | clinical variable or flag name |
| `type` | decision type |
| `n_both` | number of records labelled by both annotators |
| `n_exact_equal` | number of exactly equal label pairs |
| `raw_agreement` | raw agreement proportion |
| `cohen_kappa` | Cohen kappa |
| `gwet_ac1` | Gwet AC1 agreement coefficient |
| `a1_nonnull` | number of non-missing A1 values |
| `a2_nonnull` | number of non-missing A2 values |
| `note` | free-text note |

### `results/analysis/sensitivity_audit.csv`

| Column | Meaning |
|---|---|
| `analysis` | see the column name |
| `n` | number of records, pairs or observations analysed |
| `kappa` | Cohen kappa |
| `ci_lo` | lower bound of the 95% confidence interval |
| `ci_hi` | upper bound of the 95% confidence interval |

### `results/analysis/simex_backfill.csv`

| Column | Meaning |
|---|---|
| `outcome` | outcome definition |
| `HR_observed` | observed hazard ratio |
| `kappa_measured` | measured kappa |
| `Se_eq_Sp` | whether sensitivity equals specificity |
| `HR_corrected` | bias-corrected hazard ratio |
| `attenuation_pct` | attenuation, in percent |

### `results/analysis/simex_kappa.csv`

| Column | Meaning |
|---|---|
| `domain` | clinical domain: ECG, ECHOCARDIOGRAPHY or ABDOMINAL_ULTRASOUND |
| `n` | number of records, pairs or observations analysed |
| `prevalence_gold` | prevalence in the reference standard |
| `agreement` | agreement status or proportion |
| `cohen_kappa` | Cohen kappa |

### `results/analysis/simex_kappa_grid.csv`

| Column | Meaning |
|---|---|
| `kappa` | assumed measured kappa |
| `Se=Sp` | whether sensitivity equals specificity |
| `prevalence_pi` | assumed true prevalence |
| `HR_true` | assumed true hazard ratio |
| `HR_obs` | observed hazard ratio |
| `attenuation_pct` | attenuation, in percent |

### `results/analysis/specification_curve.csv`

| Column | Meaning |
|---|---|
| `spec` | specificity (or model specification, where the column is named spec) |
| `outcome` | outcome definition |
| `version` | phenotype definition version |
| `covset` | covariate set |
| `yearFE` | whether year fixed effects were included |
| `se_type` | standard-error estimator |
| `HR` | hazard ratio |
| `lo` | lower bound of the 95% confidence interval |
| `hi` | upper bound of the 95% confidence interval |
| `p` | two-sided p value |
| `n_risk` | number at risk |
| `n_events` | number of events |
| `sig` | whether the estimate is significant at the two-sided 0.05 level |

### `results/analysis/synthetic_cohort_specifications.csv`

| Column | Meaning |
|---|---|
| `spec` | specificity (or model specification, where the column is named spec) |
| `outcome` | outcome definition |
| `n_risk` | number at risk |
| `n_events` | number of events |
| `HR` | hazard ratio |
| `CI_lo` | lower bound of the 95% confidence interval |
| `CI_hi` | upper bound of the 95% confidence interval |
| `p` | two-sided p value |

### `results/analysis/synthetic_differential_replay.csv`

| Column | Meaning |
|---|---|
| `spec` | specificity (or model specification, where the column is named spec) |
| `n_risk` | number at risk |
| `n_events` | number of events |
| `HR` | hazard ratio |
| `CI_lo` | lower bound of the 95% confidence interval |
| `CI_hi` | upper bound of the 95% confidence interval |
| `p` | two-sided p value |
| `arm` | analysis arm or replicate arm |

### `results/analysis/text_clustered_standard_errors.csv`

| Column | Meaning |
|---|---|
| `spec` | specificity (or model specification, where the column is named spec) |
| `outcome` | outcome definition |
| `n_risk` | number at risk |
| `n_events` | number of events |
| `HR_ctv` | hazard ratio under the Cox time-varying fit |
| `CI_lo_ctv` | lower 95% CI bound under the Cox time-varying fit |
| `CI_hi_ctv` | upper 95% CI bound under the Cox time-varying fit |
| `p_ctv` | p value under the Cox time-varying fit |
| `HR_phf` | hazard ratio under the frailty model |
| `CI_lo_phf` | lower 95% CI bound under the frailty model |
| `CI_hi_phf` | upper 95% CI bound under the frailty model |
| `p_phf` | p value under the frailty model |
| `HR_robust` | hazard ratio under the robust sandwich variance |
| `CI_lo_robust` | lower 95% CI bound under the robust sandwich variance |
| `CI_hi_robust` | upper 95% CI bound under the robust sandwich variance |
| `p_robust` | p value under the robust sandwich variance |

### `results/analysis/unadjusted_sensitivity.csv`

| Column | Meaning |
|---|---|
| `spec` | specificity (or model specification, where the column is named spec) |
| `outcome` | outcome definition |
| `n_risk` | number at risk |
| `n_events` | number of events |
| `HR_crude` | unadjusted hazard ratio |
| `CI_lo` | lower bound of the 95% confidence interval |
| `CI_hi` | upper bound of the 95% confidence interval |
| `p` | two-sided p value |

### `results/analysis/version_contrast_estimates.csv`

| Column | Meaning |
|---|---|
| `contrast` | contrast being estimated |
| `B` | number of bootstrap replicates |
| `ok` | whether the replicate converged |
| `HR_v1` | hazard ratio under definition v1 |
| `HR_v3` | hazard ratio under definition v3 |
| `dHR_full` | difference in hazard ratio, full covariate set |
| `dHR_lo90` | lower 90% CI bound of the hazard-ratio difference |
| `dHR_hi90` | upper 90% CI bound of the hazard-ratio difference |
| `dHR_lo95` | lower 95% CI bound of the hazard-ratio difference |
| `dHR_hi95` | upper 95% CI bound of the hazard-ratio difference |
| `p_two_sided` | two-sided p value |
| `TOST_pm5pct` | two one-sided tests for equivalence with a +/-5% margin |

### `results/analysis/version_contrast_interaction_test.csv`

| Column | Meaning |
|---|---|
| `outcome` | outcome definition |
| `LRT_chi2` | likelihood-ratio chi-square statistic |
| `df` | degrees of freedom |
| `p` | two-sided p value |
| `n_risk` | number at risk |
| `events` | number of events |

### `results/analysis/version_contrast_peryear_hazard_ratios.csv`

| Column | Meaning |
|---|---|
| `outcome` | outcome definition |
| `year` | calendar year |
| `HR` | hazard ratio |
| `lo` | lower bound of the 95% confidence interval |
| `hi` | upper bound of the 95% confidence interval |

### `results/analysis/version_contrast_point_estimates.csv`

| Column | Meaning |
|---|---|
| `spec` | specificity (or model specification, where the column is named spec) |
| `HR` | hazard ratio |
| `lo` | lower bound of the 95% confidence interval |
| `hi` | upper bound of the 95% confidence interval |
| `n_risk` | number at risk |
| `events` | number of events |

### `results/analysis/version_replay_summary.csv`

| Column | Meaning |
|---|---|
| `arm` | analysis arm or replicate arm |
| `HR_noFE` | hazard ratio without year fixed effects |
| `HR_noFE_lo` | lower bound of the hazard ratio without year fixed effects |
| `HR_noFE_hi` | upper bound of the hazard ratio without year fixed effects |
| `n_risk_noFE` | see the column name |
| `events_noFE` | see the column name |
| `HR_yearFE` | hazard ratio with year fixed effects |
| `HR_yearFE_lo` | lower 95% CI bound of HR_yearFE |
| `HR_yearFE_hi` | upper 95% CI bound of HR_yearFE |
| `n_risk_yearFE` | see the column name |
| `events_yearFE` | see the column name |
| `R` | number of replicates |

### `results/analysis/version_replay_year_parameters.csv`

| Column | Meaning |
|---|---|
| `year` | calendar year |
| `n` | number of records, pairs or observations analysed |
| `pi_true` | see the column name |
| `Se` | sensitivity |
| `Sp` | specificity |
| `p_obs_pos` | see the column name |

### `results/analysis/wilson_ci_gates.csv`

| Column | Meaning |
|---|---|
| `domain` | clinical domain: ECG, ECHOCARDIOGRAPHY or ABDOMINAL_ULTRASOUND |
| `model` | model name or version |
| `variable` | clinical variable or flag name |
| `target_class` | target class for the Wilson interval |
| `n` | number of records, pairs or observations analysed |
| `TP` | true positives |
| `FP` | false positives |
| `FN` | false negatives |
| `F1` | F1 score |
| `Wilson_lo` | lower Wilson confidence bound |
| `Wilson_hi` | upper Wilson confidence bound |
| `gate` | prespecified acceptance gate |
| `CI_contains_gate` | whether the interval contains the gate value |
| `CI_excludes_gate_below` | whether the interval excludes the gate from below |
| `CI_excludes_gate_above` | whether the interval excludes the gate from above |

## External-validation tables (results/external-site/)

### `results/external-site/dictionary_flags_abdomen.csv`

| Column | Meaning |
|---|---|
| `sample_id` | deidentified record identifier |
| `year` | calendar year |
| `stratum` | sampling or analysis stratum |
| `input_sha256` | SHA-256 of the input text |
| `us_fatty` | fatty liver present |
| `us_fatty_degree` | fatty liver grade (0-3) |
| `us_hepatic_other` | other hepatic finding |
| `us_gallstone` | gallstone present |
| `us_kidney_cyst` | kidney cyst present |
| `us_unreadable` | ultrasound report unreadable |
| `_stone_strict` | strict gallstone criterion applied |
| `_cyst_large` | large-cyst criterion applied |
| `_post_chole` | post-cholecystectomy criterion applied |
| `_focal_liver` | focal liver lesion criterion applied |
| `_polyp` | polyp criterion applied |
| `outcome_dict` | dictionary-track outcome (0 normal, 1 indeterminate, 2 abnormal) |

### `results/external-site/dictionary_flags_ecg.csv`

| Column | Meaning |
|---|---|
| `sample_id` | deidentified record identifier |
| `year` | calendar year |
| `stratum` | sampling or analysis stratum |
| `input_sha256` | SHA-256 of the input text |
| `ecg_normal` | normal ECG |
| `ecg_af` | atrial fibrillation |
| `ecg_pac_pvc` | premature atrial or ventricular contraction |
| `ecg_stt` | ST-T abnormality |
| `ecg_avblock` | atrioventricular block |
| `ecg_bbb` | bundle-branch block |
| `ecg_rate` | heart-rate abnormality |
| `ecg_srirr` | sinus rhythm or irregular rhythm |
| `ecg_axis` | axis deviation |
| `ecg_qwave_mi` | Q wave or myocardial infarction |
| `ecg_other` | other ECG finding |
| `ecg_unreadable` | ECG unreadable |
| `outcome_dict` | dictionary-track outcome (0 normal, 1 indeterminate, 2 abnormal) |

### `results/external-site/domain_confusion_matrix_by_annotator.csv`

| Column | Meaning |
|---|---|
| `域` | clinical domain |
| `track` | extraction track |
| `定义` | phenotype definition |
| `人工` | clinician judgement |
| `系统0` | records classified 0 by the system |
| `系统1` | records classified 1 by the system |
| `系统2` | records classified 2 by the system |

### `results/external-site/domain_flag_level_performance.csv`

| Column | Meaning |
|---|---|
| `域` | clinical domain |
| `track` | extraction track |
| `flag` | whether the annotators disagreed |
| `阳性定义` | positive-class definition |
| `n` | number of records, pairs or observations analysed |
| `人工阳性` | records positive by clinicians |
| `系统阳性` | records positive by the system |
| `TP` | true positives |
| `FP` | false positives |
| `FN` | false negatives |
| `原始一致率` | raw agreement |
| `Cohen_κ` | Cohen kappa |
| `Gwet_AC1` | Gwet AC1 agreement coefficient |
| `precision` | precision (positive predictive value) |
| `recall` | recall (sensitivity for the positive class) |
| `F1` | F1 score |

### `results/external-site/domain_performance_by_year.csv`

| Column | Meaning |
|---|---|
| `域` | clinical domain |
| `track` | extraction track |
| `定义` | phenotype definition |
| `年` | calendar year |
| `抽样层` | sampling stratum |
| `n` | number of records, pairs or observations analysed |
| `人工0` | records judged 0 (normal) by clinicians |
| `人工1` | records judged 1 (indeterminate) by clinicians |
| `人工2` | records judged 2 (abnormal) by clinicians |
| `Sens` | sensitivity |
| `Spec` | specificity |
| `F1` | F1 score |
| `κ` | Cohen kappa |
| `一致率` | agreement proportion |
| `备注` | note |

### `results/external-site/domain_performance_metrics.csv`

| Column | Meaning |
|---|---|
| `域` | clinical domain |
| `track` | extraction track |
| `定义` | phenotype definition |
| `n` | number of records, pairs or observations analysed |
| `人工0` | records judged 0 (normal) by clinicians |
| `人工1` | records judged 1 (indeterminate) by clinicians |
| `人工2` | records judged 2 (abnormal) by clinicians |
| `系统0` | records classified 0 by the system |
| `系统1` | records classified 1 by the system |
| `系统2` | records classified 2 by the system |
| `TP` | true positives |
| `FP` | false positives |
| `FN` | false negatives |
| `TN` | true negatives |
| `Sens` | sensitivity |
| `Sens_lo` | lower 95% CI bound of Sens |
| `Sens_hi` | upper 95% CI bound of Sens |
| `Spec` | specificity |
| `Spec_lo` | lower 95% CI bound of Spec |
| `Spec_hi` | upper 95% CI bound of Spec |
| `PPV` | positive predictive value |
| `PPV_lo` | lower 95% CI bound of PPV |
| `PPV_hi` | upper 95% CI bound of PPV |
| `NPV` | negative predictive value |
| `NPV_lo` | lower 95% CI bound of NPV |
| `NPV_hi` | upper 95% CI bound of NPV |
| `F1` | F1 score |
| `F1_lo` | lower 95% CI bound of F1 |
| `F1_hi` | upper 95% CI bound of F1 |
| `κ` | Cohen kappa |
| `κ_lo` | lower 95% CI bound of kappa |
| `κ_hi` | upper 95% CI bound of kappa |
| `原始一致率` | raw agreement |
| `一致率_Wilson_lo` | lower Wilson bound of raw agreement |
| `一致率_Wilson_hi` | upper Wilson bound of raw agreement |
| `H1` | whether the prespecified H1 criterion was met |
| `H1_注册文本口径` | H1 evaluated under the registered wording |

### `results/external-site/domain_record_outcomes.csv`

| Column | Meaning |
|---|---|
| `域` | clinical domain |
| `sample_id` | deidentified record identifier |
| `年` | calendar year |
| `抽样层` | sampling stratum |
| `人工outcome` | clinician panel outcome |
| `词典outcome` | dictionary-track outcome |
| `LLM_outcome` | language-model outcome |
| `词典naive` | dictionary-track naive outcome |
| `LLM_naive` | language-model naive outcome |
| `词典正确` | whether the dictionary-track outcome is correct |
| `LLM正确` | whether the language-model outcome is correct |

### `results/external-site/domain_unreadable_summary.csv`

| Column | Meaning |
|---|---|
| `域` | clinical domain |
| `track` | extraction track |
| `n` | number of records, pairs or observations analysed |
| `人工不可判读_outcome0` | records marked unreadable (outcome 0) by clinicians |
| `系统判为不可判读_n` | number of records the system marked unreadable |
| `TP` | true positives |
| `FP` | false positives |
| `FN` | false negatives |
| `检出率` | detection rate |
| `人工不可判读_sample_id` | identifiers of records marked unreadable by clinicians |
| `系统判为不可判读_sample_id` | identifiers of records the system marked unreadable |

### `results/external-site/intra_rater_annotator_summary.csv`

| Column | Meaning |
|---|---|
| `域` | clinical domain |
| `标注员` | annotator |
| `n` | number of records, pairs or observations analysed |
| `raw agreement` | raw agreement proportion |
| `Cohen κ` | Cohen kappa |
| `Gwet AC1` | see the column name |
| `门 κ≥0.85` | gate of kappa >= 0.85 |

### `results/external-site/intra_rater_field_kappa.csv`

| Column | Meaning |
|---|---|
| `域` | clinical domain |
| `标注员` | annotator |
| `字段` | annotation field |
| `字段代码` | field code |
| `可比 n` | number of comparable pairs |
| `raw agreement` | raw agreement proportion |
| `Cohen κ` | Cohen kappa |
| `Gwet AC1` | see the column name |
| `首轮分布` | first-round label distribution |
| `重标分布` | repeat-annotation label distribution |
| `参考≥0.85` | reference threshold of kappa >= 0.85 |
| `备注` | note |

### `results/external-site/intra_rater_qc_checks.csv`

| Column | Meaning |
|---|---|
| `域` | clinical domain |
| `序号` | check number |
| `检查项` | quality-control check |
| `合格标准` | acceptance criterion |
| `结果` | result |
| `证据` | evidence |

### `results/external-site/intra_rater_relabel_basis.csv`

| Column | Meaning |
|---|---|
| `域` | clinical domain |
| `标注员` | annotator |
| `字段` | annotation field |
| `SR 编号` | self-repeat record identifier |
| `来源 SB 编号` | source record identifier in the first round |
| `首轮` | first-round label |
| `重标` | repeat-annotation label |
| `重标依据词句` | text span supporting the repeat label |

### `results/external-site/model_outputs_abdomen.csv`

| Column | Meaning |
|---|---|
| `sample_id` | deidentified record identifier |
| `input_hash` | SHA-256 of the input text |
| `output_hash` | SHA-256 of the model output |
| `prompt_sha16` | first 16 hex characters of the prompt fingerprint |
| `error` | error type or message |
| `model_output_json` | raw model output as JSON |

### `results/external-site/model_outputs_ecg.csv`

| Column | Meaning |
|---|---|
| `sample_id` | deidentified record identifier |
| `input_hash` | SHA-256 of the input text |
| `output_hash` | SHA-256 of the model output |
| `prompt_sha16` | first 16 hex characters of the prompt fingerprint |
| `error` | error type or message |
| `model_output_json` | raw model output as JSON |

### `results/external-site/text_cluster_kappa.csv`

| Column | Meaning |
|---|---|
| `domain` | clinical domain: ECG, ECHOCARDIOGRAPHY or ABDOMINAL_ULTRASOUND |
| `track` | extraction track |
| `n_records` | number of records |
| `n_unique_texts` | number of unique narrative texts |
| `redundancy` | text redundancy ratio |
| `kappa` | Cohen kappa |
| `ci_low` | lower bound of the bootstrap confidence interval |
| `ci_high` | upper bound of the bootstrap confidence interval |
| `ci_record_low` | lower record-level bootstrap CI bound |
| `ci_record_high` | upper record-level bootstrap CI bound |
| `se_cluster` | cluster-robust standard error |
| `se_record` | record-level standard error |
| `design_effect` | design effect from text clustering |
| `kappa_unique_text` | kappa restricted to unique texts |
| `n_unique_eval` | unique texts used in the kappa evaluation |

## Inter-rater agreement cells (results/agreement/)

### `results/agreement/inter_rater_cells_abdomen_hospital.csv`

| Column | Meaning |
|---|---|
| `variable` | clinical variable or flag name |
| `n` | number of records, pairs or observations analysed |
| `raw_agreement` | raw agreement proportion |
| `cohen_kappa` | Cohen kappa |
| `gwet_ac1` | Gwet AC1 agreement coefficient |
| `prec_0` | precision for class 0 |
| `rec_0` | recall for class 0 |
| `F1_0` | F1 for class 0 |
| `prec_1` | precision for class 1 |
| `rec_1` | recall for class 1 |
| `F1_1` | F1 for class 1 |

### `results/agreement/inter_rater_cells_abdomen_primary.csv`

| Column | Meaning |
|---|---|
| `variable` | clinical variable or flag name |
| `n` | number of records, pairs or observations analysed |
| `raw_agreement` | raw agreement proportion |
| `cohen_kappa` | Cohen kappa |
| `gwet_ac1` | Gwet AC1 agreement coefficient |
| `prec_0` | precision for class 0 |
| `rec_0` | recall for class 0 |
| `F1_0` | F1 for class 0 |
| `prec_1` | precision for class 1 |
| `rec_1` | recall for class 1 |
| `F1_1` | F1 for class 1 |

### `results/agreement/inter_rater_cells_ecg.csv`

| Column | Meaning |
|---|---|
| `variable` | clinical variable or flag name |
| `n` | number of records, pairs or observations analysed |
| `raw_agreement` | raw agreement proportion |
| `cohen_kappa` | Cohen kappa |
| `gwet_ac1` | Gwet AC1 agreement coefficient |
| `prec_0` | precision for class 0 |
| `rec_0` | recall for class 0 |
| `F1_0` | F1 for class 0 |
| `prec_1` | precision for class 1 |
| `rec_1` | recall for class 1 |
| `F1_1` | F1 for class 1 |

### `results/agreement/inter_rater_cells_echocardiography.csv`

| Column | Meaning |
|---|---|
| `variable` | clinical variable or flag name |
| `n` | number of records, pairs or observations analysed |
| `raw_agreement` | raw agreement proportion |
| `cohen_kappa` | Cohen kappa |
| `gwet_ac1` | Gwet AC1 agreement coefficient |
| `prec_0` | precision for class 0 |
| `rec_0` | recall for class 0 |
| `F1_0` | F1 for class 0 |
| `prec_1` | precision for class 1 |
| `rec_1` | recall for class 1 |
| `F1_1` | F1 for class 1 |

