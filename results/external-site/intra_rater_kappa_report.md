# External-site intra-rater kappa report

Self-repeat (test-retest) intra-rater kappa analysis, material returned 2026-10-24.

Specification lock: the first blinded annotation and this repeat annotation both used annotation manual V3.1 plus the external-site appendix; no re-adjudication under V4.0 (kappa measures reading stability, and a definition change would invalidate it). Sample: 30 ECG and 30 abdomen records (10% of the 300 per domain); annotators A1 and A2 each relabelled the same records, renumbered SRECG/SRABD-001 to 030. Timing: first round returned 2026-10-19, repeat released to annotators 2026-10-22, re-annotation returned 2026-10-24 (5-day interval, >= 3 days). Prespecified gate: outcome intra-rater kappa >= 0.85 per domain and per annotator (the quality gate precedes unblinding, and the unblinded comparison waits for this gate).

Verification: 11 items x 2 domains = 22 items, 22/22 pass, 0 failures; verification conclusion: pass. Kappa gate: 4 outcome items (ECG/abdomen x A1/A2), 4/4 pass. ECG: A1 kappa = 1.000 (raw = 1.000, n = 30); A2 kappa = 1.000 (raw = 1.000, n = 30). Abdomen: A1 kappa = 1.000 (raw = 1.000, n = 30); A2 kappa = 0.939 (raw = 0.967, n = 30).

Statistical notes:

1. Cohen kappa (unweighted, nominal scale); Gwet AC1 is a mandatory sensitivity metric because the external-site text is highly repetitive (prevalence paradox).
2. When the marginal distribution is degenerate (the same category in both rounds, pe approximately 1): complete agreement is recorded as kappa = 1.000 with raw agreement, and disagreement is recorded as not estimable without a point estimate.
3. us_fatty_degree pairs skip records that are empty in both rounds (the same rule as blinded-annotation verification); empty binary flags are treated as 0 following the external-site convention (missing instances are counted in verification item 5).
4. Flag-level kappa is reported for reference only with no hard gate; the gate applies to the outcome only (protocol section 5, frozen).

Conclusion: outcome intra-rater kappa 4/4 >= 0.85, self-repeat reading stability is established, the kappa gate passes, and the unblinded comparison run may proceed (protocol section 5, item 4). One outcome-level disagreement: abdomen/A2 SRABD-009 (first round 1, repeat 0). If flag-level kappa is not estimable or departs from the gate because of marginal degeneracy, agreement and AC1 are reported as observed without adjustment.
