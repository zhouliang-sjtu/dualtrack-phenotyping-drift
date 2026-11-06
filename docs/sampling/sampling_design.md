# Sampling design for the reference standard

The reference standard was drawn by stratified random sampling with a fixed seed (42) from each source's eligible records.

| Domain | Frame | Sampling strata | n |
|---|---|---|---|
| ECG | 121,220 classifiable ECG narratives, 2018-2024 | calendar year x rare-keyword stratum | 570 |
| Echocardiography | rule-stratified parent frame (600 reports) | rule class, nested subset | 300 |
| Abdominal ultrasound, primary-care site | eligible reports at that site | rule class | 300 |
| Abdominal ultrasound, hospital site | eligible reports at that site | rule class | 300 |

All records were pseudonymised before delivery, full-text masking was applied, and no narrative text left the institution. Per-record narrative text is not redistributed; the deposited label file retains record identifiers and both annotators' labels.

An additional 160-record adjudication sample was drawn from the 2023 definition-divergence stratum and three anchor strata to resolve the monitoring alarm; see `data/adjudication/adjudication_dataset_160.csv`.
