# TypedDecide Benchmark Report

Authored 190-case, 19-family fixture; 4 backends; 5 repeat(s). This is exploratory and does not establish broad model superiority.

## Overall

| Backend  | Accuracy |  Brier |    NLL | Score MAE | Mean latency ms | Failures |
| -------- | -------: | -----: | -----: | --------: | --------------: | -------: |
| jev      |    97.9% | 0.0347 | 0.0684 |    0.0053 |           275.9 |        0 |
| thisthat |    80.0% | 0.3308 | 0.8319 |    0.2021 |           136.5 |        0 |
| laya     |    54.7% | 0.5424 | 0.9349 |    0.7417 |            58.7 |        0 |
| semif    |    88.9% | 0.1581 | 0.2705 |    0.1236 |           179.6 |        0 |

## By Family

| Group                |    jev | thisthat |  laya |  semif |
| -------------------- | -----: | -------: | ----: | -----: |
| access_policy        | 100.0% |    50.0% | 50.0% |  90.0% |
| agent_orchestration  | 100.0% |    90.0% | 60.0% |  50.0% |
| command_risk         | 100.0% |   100.0% | 70.0% | 100.0% |
| entity_matching      | 100.0% |    80.0% | 90.0% |  70.0% |
| evidence_support     | 100.0% |   100.0% | 80.0% | 100.0% |
| exception_scope      | 100.0% |    80.0% | 50.0% |  90.0% |
| incident_severity    | 100.0% |   100.0% | 80.0% | 100.0% |
| narrative_security   |  80.0% |    70.0% | 60.0% | 100.0% |
| passage_relevance    | 100.0% |    70.0% | 60.0% | 100.0% |
| record_linkage       | 100.0% |    70.0% | 40.0% |  90.0% |
| refund_eligibility   | 100.0% |    80.0% | 70.0% | 100.0% |
| security_triage      | 100.0% |    90.0% | 40.0% | 100.0% |
| spatial_anomaly      | 100.0% |    90.0% | 40.0% | 100.0% |
| structured_lookup    | 100.0% |    90.0% | 20.0% |  90.0% |
| support_routing      | 100.0% |    80.0% | 90.0% | 100.0% |
| thread_routing       |  90.0% |    70.0% | 20.0% |  80.0% |
| tool_call_validation | 100.0% |    70.0% | 70.0% |  80.0% |
| tool_selection       |  90.0% |    40.0% | 30.0% |  50.0% |
| value_selection      | 100.0% |   100.0% | 20.0% | 100.0% |

## By Primitive

| Group  |    jev | thisthat |  laya |  semif |
| ------ | -----: | -------: | ----: | -----: |
| choice |  95.1% |    87.7% | 48.1% |  88.9% |
| noul   | 100.0% |    68.2% | 57.6% |  81.8% |
| score  | 100.0% |    83.7% | 62.8% | 100.0% |

## Case Results

| Case                                      | Family               | Gold              | jev                         | thisthat                    | laya                         | semif                       |
| ----------------------------------------- | -------------------- | ----------------- | --------------------------- | --------------------------- | ---------------------------- | --------------------------- |
| support-routing-billing                   | support_routing      | billing           | OK billing (1.00)           | OK billing (1.00)           | OK billing (0.63)            | OK billing (0.99)           |
| support-routing-account                   | support_routing      | account           | OK account (1.00)           | OK account (1.00)           | OK account (0.73)            | OK account (1.00)           |
| support-routing-other                     | support_routing      | other             | OK other (1.00)             | OK other (1.00)             | OK other (0.66)              | OK other (0.98)             |
| refund-eligible-damaged                   | refund_eligibility   | true              | OK true (0.98)              | ERR false (0.92)            | OK true (0.54)               | OK true (0.98)              |
| refund-ineligible-final-sale              | refund_eligibility   | false             | OK false (0.96)             | OK false (1.00)             | OK false (0.51)              | OK false (0.95)             |
| refund-ineligible-day-31                  | refund_eligibility   | false             | OK false (0.96)             | OK false (0.99)             | ERR true (0.54)              | OK false (0.94)             |
| command-risk-read-only                    | command_risk         | read_only         | OK read_only (1.00)         | OK read_only (1.00)         | OK read_only (0.42)          | OK read_only (1.00)         |
| command-risk-destructive                  | command_risk         | destructive       | OK destructive (1.00)       | OK destructive (1.00)       | OK destructive (0.67)        | OK destructive (1.00)       |
| command-risk-network                      | command_risk         | network           | OK network (1.00)           | OK network (0.99)           | OK network (0.55)            | OK network (1.00)           |
| access-allowed-owner                      | access_policy        | true              | OK true (0.98)              | OK true (1.00)              | OK true (0.66)               | OK true (0.99)              |
| access-denied-other-employee              | access_policy        | false             | OK false (0.94)             | ERR true (0.55)             | ERR true (0.61)              | OK false (0.97)             |
| access-allowed-admin                      | access_policy        | true              | OK true (0.98)              | OK true (1.00)              | OK true (0.63)               | OK true (0.91)              |
| incident-severity-low                     | incident_severity    | low               | OK low (1.00)               | OK low (1.00)               | ERR medium (0.52)            | OK low (1.00)               |
| incident-severity-medium                  | incident_severity    | medium            | OK medium (1.00)            | OK medium (0.99)            | OK medium (0.64)             | OK medium (0.99)            |
| incident-severity-critical                | incident_severity    | critical          | OK critical (1.00)          | OK critical (0.95)          | OK critical (0.64)           | OK critical (0.99)          |
| evidence-supported                        | evidence_support     | supported         | OK supported (0.98)         | OK supported (0.99)         | OK supported (0.58)          | OK supported (1.00)         |
| evidence-contradicted                     | evidence_support     | contradicted      | OK contradicted (1.00)      | OK contradicted (0.99)      | ERR supported (0.60)         | OK contradicted (0.95)      |
| evidence-insufficient                     | evidence_support     | insufficient      | OK insufficient (1.00)      | OK insufficient (0.98)      | OK insufficient (0.76)       | OK insufficient (0.99)      |
| entity-match-strong                       | entity_matching      | true              | OK true (0.97)              | OK true (0.97)              | OK true (0.51)               | OK true (0.85)              |
| entity-match-conflict                     | entity_matching      | false             | OK false (0.92)             | OK false (0.72)             | OK false (0.78)              | ERR true (0.59)             |
| entity-match-boundary                     | entity_matching      | true              | OK true (0.96)              | OK true (1.00)              | OK true (0.75)               | OK true (0.88)              |
| value-selection-invoice-total             | value_selection      | candidate_3       | OK candidate_3 (1.00)       | OK candidate_3 (1.00)       | ERR candidate_1 (0.33)       | OK candidate_3 (0.98)       |
| value-selection-tax                       | value_selection      | candidate_2       | OK candidate_2 (1.00)       | OK candidate_2 (1.00)       | ERR candidate_1 (0.37)       | OK candidate_2 (0.98)       |
| value-selection-none                      | value_selection      | none              | OK none (0.99)              | OK none (1.00)              | ERR candidate_2 (0.35)       | OK none (0.93)              |
| passage-relevance-direct                  | passage_relevance    | direct            | OK direct (1.00)            | OK direct (0.99)            | OK direct (0.64)             | OK direct (0.97)            |
| passage-relevance-partial                 | passage_relevance    | partial           | OK partial (1.00)           | ERR direct (0.98)           | ERR direct (0.59)            | OK partial (0.70)           |
| passage-relevance-irrelevant              | passage_relevance    | irrelevant        | OK irrelevant (0.99)        | OK irrelevant (0.74)        | OK irrelevant (0.42)         | OK irrelevant (1.00)        |
| tool-call-valid                           | tool_call_validation | true              | OK true (0.98)              | OK true (1.00)              | ERR false (0.69)             | OK true (0.98)              |
| tool-call-wrong-unit                      | tool_call_validation | false             | OK false (0.96)             | ERR true (0.98)             | OK false (0.60)              | OK false (0.96)             |
| tool-call-missing-date                    | tool_call_validation | false             | OK false (0.94)             | OK false (0.99)             | OK false (0.58)              | ERR true (0.89)             |
| support-routing-orders-delivery           | support_routing      | orders            | OK orders (1.00)            | OK orders (0.99)            | OK orders (0.49)             | OK orders (1.00)            |
| support-routing-billing-invoice           | support_routing      | billing           | OK billing (1.00)           | OK billing (1.00)           | OK billing (0.78)            | OK billing (1.00)           |
| support-routing-account-permission        | support_routing      | account           | OK account (0.99)           | ERR other (1.00)            | OK account (0.48)            | OK account (0.98)           |
| support-routing-orders-cancel             | support_routing      | orders            | OK orders (1.00)            | OK orders (1.00)            | OK orders (0.82)             | OK orders (1.00)            |
| support-routing-urgency-refund-delay      | support_routing      | critical          | OK critical (0.98)          | ERR high (0.56)             | ERR high (0.49)              | OK critical (0.96)          |
| support-routing-billing-refund-status     | support_routing      | billing           | OK billing (1.00)           | OK billing (0.99)           | OK billing (0.73)            | OK billing (1.00)           |
| support-routing-orders-return             | support_routing      | orders            | OK orders (1.00)            | OK orders (0.99)            | OK orders (0.55)             | OK orders (0.99)            |
| refund-evidence-strength-damaged-day-30   | refund_eligibility   | conclusive        | OK conclusive (1.00)        | OK conclusive (0.86)        | OK conclusive (0.45)         | OK conclusive (0.97)        |
| refund-ineligible-undamaged               | refund_eligibility   | false             | OK false (0.97)             | OK false (1.00)             | OK false (0.50)              | OK false (0.99)             |
| refund-eligible-day-zero                  | refund_eligibility   | true              | OK true (0.98)              | OK true (0.92)              | OK true (0.56)               | OK true (0.99)              |
| refund-ineligible-day-45                  | refund_eligibility   | false             | OK false (0.96)             | OK false (0.98)             | ERR true (0.52)              | OK false (0.99)             |
| refund-ineligible-final-sale-day-one      | refund_eligibility   | false             | OK false (0.96)             | OK false (0.99)             | OK false (0.52)              | OK false (0.93)             |
| refund-eligible-day-14                    | refund_eligibility   | true              | OK true (0.98)              | ERR false (0.77)            | ERR false (0.52)             | OK true (0.99)              |
| refund-ineligible-no-refund-request       | refund_eligibility   | false             | OK false (0.94)             | OK false (0.92)             | OK false (0.62)              | OK false (0.53)             |
| command-risk-mutating-mkdir               | command_risk         | mutating          | OK mutating (1.00)          | OK mutating (0.99)          | OK mutating (0.52)           | OK mutating (0.98)          |
| command-risk-read-only-processes          | command_risk         | read_only         | OK read_only (1.00)         | OK read_only (0.99)         | ERR mutating (0.45)          | OK read_only (0.98)         |
| command-risk-mutating-chmod               | command_risk         | mutating          | OK mutating (1.00)          | OK mutating (0.99)          | OK mutating (0.54)           | OK mutating (0.97)          |
| command-risk-destructive-stop-database    | command_risk         | destructive       | OK destructive (0.92)       | OK destructive (0.99)       | OK destructive (0.52)        | OK destructive (0.79)       |
| command-risk-network-scp                  | command_risk         | network           | OK network (1.00)           | OK network (1.00)           | OK network (0.41)            | OK network (0.99)           |
| command-risk-destructive-overwrite-disk   | command_risk         | destructive       | OK destructive (1.00)       | OK destructive (0.94)       | ERR mutating (0.33)          | OK destructive (0.99)       |
| command-risk-score-overwrite-disk         | command_risk         | critical          | OK critical (1.00)          | OK critical (0.86)          | ERR high (0.49)              | OK critical (1.00)          |
| access-sensitivity-payroll-record         | access_policy        | restricted        | OK restricted (1.00)        | OK restricted (0.66)        | OK restricted (0.35)         | OK restricted (0.99)        |
| access-denied-write-own                   | access_policy        | false             | OK false (0.95)             | ERR true (0.97)             | OK false (0.51)              | OK false (0.96)             |
| access-denied-contractor                  | access_policy        | false             | OK false (0.95)             | OK false (1.00)             | ERR true (0.56)              | OK false (0.68)             |
| access-allowed-admin-two                  | access_policy        | true              | OK true (0.98)              | OK true (1.00)              | OK true (0.62)               | OK true (0.87)              |
| access-denied-employee-third-party        | access_policy        | false             | OK false (0.94)             | ERR true (0.94)             | ERR true (0.61)              | OK false (0.95)             |
| access-denied-admin-write                 | access_policy        | false             | OK false (0.91)             | ERR true (1.00)             | ERR true (0.52)              | OK false (0.93)             |
| access-denied-unknown-role                | access_policy        | false             | OK false (0.93)             | ERR true (0.59)             | ERR true (0.61)              | ERR true (0.82)             |
| incident-severity-high-login              | incident_severity    | high              | OK high (0.96)              | OK high (1.00)              | OK high (0.48)               | OK high (0.89)              |
| incident-severity-medium-search           | incident_severity    | medium            | OK medium (1.00)            | OK medium (1.00)            | OK medium (0.66)             | OK medium (0.98)            |
| incident-severity-low-typo                | incident_severity    | low               | OK low (1.00)               | OK low (0.99)               | OK low (0.42)                | OK low (1.00)               |
| incident-severity-critical-data-loss      | incident_severity    | critical          | OK critical (1.00)          | OK critical (0.99)          | OK critical (0.60)           | OK critical (0.98)          |
| incident-severity-high-checkout           | incident_severity    | high              | OK high (1.00)              | OK high (1.00)              | OK high (0.46)               | OK high (0.99)              |
| incident-severity-medium-email            | incident_severity    | medium            | OK medium (1.00)            | OK medium (0.99)            | OK medium (0.59)             | OK medium (0.96)            |
| incident-severity-critical-total-outage   | incident_severity    | critical          | OK critical (1.00)          | OK critical (1.00)          | ERR high (0.47)              | OK critical (0.77)          |
| evidence-supported-release-date           | evidence_support     | supported         | OK supported (1.00)         | OK supported (0.83)         | OK supported (0.89)          | OK supported (1.00)         |
| evidence-contradicted-release-date        | evidence_support     | contradicted      | OK contradicted (1.00)      | OK contradicted (0.99)      | OK contradicted (0.87)       | OK contradicted (0.98)      |
| evidence-strength-release-date            | evidence_support     | direct            | OK direct (0.99)            | OK direct (0.73)            | OK direct (0.75)             | OK direct (0.94)            |
| evidence-supported-policy                 | evidence_support     | supported         | OK supported (1.00)         | OK supported (0.97)         | OK supported (0.63)          | OK supported (1.00)         |
| evidence-contradicted-policy              | evidence_support     | contradicted      | OK contradicted (1.00)      | OK contradicted (1.00)      | OK contradicted (0.87)       | OK contradicted (1.00)      |
| evidence-insufficient-carryover           | evidence_support     | insufficient      | OK insufficient (1.00)      | OK insufficient (0.99)      | OK insufficient (0.77)       | OK insufficient (0.99)      |
| evidence-supported-capacity               | evidence_support     | supported         | OK supported (0.94)         | OK supported (0.99)         | ERR insufficient (0.55)      | OK supported (0.85)         |
| entity-match-same-customer-id             | entity_matching      | true              | OK true (0.99)              | OK true (0.95)              | OK true (0.56)               | OK true (0.73)              |
| entity-match-confidence-shared-identifier | entity_matching      | high              | OK high (1.00)              | OK high (1.00)              | OK high (0.46)               | OK high (0.96)              |
| entity-match-email-format                 | entity_matching      | true              | OK true (0.98)              | OK true (0.99)              | OK true (0.78)               | OK true (0.84)              |
| entity-match-different-email              | entity_matching      | false             | OK false (0.83)             | ERR true (0.75)             | OK false (0.52)              | ERR true (0.65)             |
| entity-match-phone-normalization          | entity_matching      | true              | OK true (0.97)              | OK true (0.99)              | OK true (0.73)               | OK true (0.90)              |
| entity-match-different-phone              | entity_matching      | false             | OK false (0.89)             | ERR true (0.82)             | OK false (0.55)              | ERR true (0.75)             |
| entity-match-employee-id                  | entity_matching      | true              | OK true (0.96)              | OK true (0.97)              | ERR false (0.57)             | OK true (0.53)              |
| value-selection-due-date                  | value_selection      | candidate_2       | OK candidate_2 (1.00)       | OK candidate_2 (1.00)       | ERR candidate_1 (0.49)       | OK candidate_2 (1.00)       |
| value-selection-issue-date                | value_selection      | candidate_1       | OK candidate_1 (1.00)       | OK candidate_1 (1.00)       | OK candidate_1 (0.54)        | OK candidate_1 (1.00)       |
| value-selection-support-email             | value_selection      | candidate_2       | OK candidate_2 (1.00)       | OK candidate_2 (1.00)       | ERR candidate_1 (0.62)       | OK candidate_2 (0.99)       |
| value-selection-privacy-email             | value_selection      | candidate_3       | OK candidate_3 (1.00)       | OK candidate_3 (1.00)       | ERR candidate_1 (0.52)       | OK candidate_3 (1.00)       |
| value-selection-phone                     | value_selection      | candidate_2       | OK candidate_2 (1.00)       | OK candidate_2 (1.00)       | ERR candidate_1 (0.57)       | OK candidate_2 (0.99)       |
| value-extraction-answerability-budget     | value_selection      | complete          | OK complete (1.00)          | OK complete (1.00)          | OK complete (0.71)           | OK complete (0.98)          |
| value-selection-budget                    | value_selection      | candidate_2       | OK candidate_2 (1.00)       | OK candidate_2 (1.00)       | ERR candidate_1 (0.61)       | OK candidate_2 (0.99)       |
| passage-relevance-context-only            | passage_relevance    | context_only      | OK context_only (1.00)      | OK context_only (0.74)      | ERR direct (0.38)            | OK context_only (0.73)      |
| passage-relevance-direct-password         | passage_relevance    | direct            | OK direct (0.99)            | OK direct (0.90)            | OK direct (0.51)             | OK direct (0.98)            |
| passage-relevance-partial-password        | passage_relevance    | partial           | OK partial (1.00)           | OK partial (0.81)           | OK partial (0.33)            | OK partial (0.72)           |
| passage-relevance-irrelevant-password     | passage_relevance    | irrelevant        | OK irrelevant (1.00)        | ERR context_only (0.59)     | OK irrelevant (0.91)         | OK irrelevant (1.00)        |
| passage-relevance-context-only-refund     | passage_relevance    | context_only      | OK context_only (0.99)      | OK context_only (0.92)      | ERR partial (0.45)           | OK context_only (0.95)      |
| passage-relevance-direct-refund           | passage_relevance    | direct            | OK direct (1.00)            | OK direct (0.99)            | OK direct (0.72)             | OK direct (0.97)            |
| passage-relevance-partial-export          | passage_relevance    | partial           | OK partial (1.00)           | ERR direct (0.72)           | ERR direct (0.52)            | OK partial (0.81)           |
| tool-call-valid-stock                     | tool_call_validation | true              | OK true (0.99)              | OK true (1.00)              | ERR false (0.66)             | OK true (0.99)              |
| tool-call-wrong-warehouse                 | tool_call_validation | false             | OK false (0.97)             | OK false (0.97)             | OK false (0.54)              | OK false (0.88)             |
| tool-call-missing-sku                     | tool_call_validation | false             | OK false (0.97)             | ERR true (1.00)             | OK false (0.77)              | OK false (0.53)             |
| tool-call-completeness-inventory          | tool_call_validation | verified          | OK verified (1.00)          | OK verified (1.00)          | OK verified (0.46)           | OK verified (0.95)          |
| tool-call-valid-email                     | tool_call_validation | true              | OK true (0.93)              | OK true (1.00)              | ERR false (0.64)             | OK true (0.99)              |
| tool-call-wrong-recipient                 | tool_call_validation | false             | OK false (0.97)             | OK false (0.97)             | OK false (0.57)              | OK false (0.91)             |
| tool-call-missing-subject                 | tool_call_validation | false             | OK false (0.95)             | ERR true (1.00)             | OK false (0.61)              | ERR true (0.59)             |
| spatial-anomaly-within-limits             | spatial_anomaly      | false             | OK false (0.94)             | OK false (1.00)             | OK false (0.75)              | OK false (0.80)             |
| spatial-anomaly-unexplained-detour        | spatial_anomaly      | true              | OK true (0.98)              | OK true (1.00)              | ERR false (0.74)             | OK true (0.93)              |
| spatial-severity-within-band              | spatial_anomaly      | low               | OK low (0.98)               | OK low (1.00)               | ERR high (0.38)              | OK low (0.86)               |
| spatial-severity-gps-gap                  | spatial_anomaly      | moderate          | OK moderate (1.00)          | OK moderate (0.99)          | ERR high (0.41)              | OK moderate (0.58)          |
| spatial-severity-unexplained-stop         | spatial_anomaly      | high              | OK high (0.89)              | ERR moderate (0.56)         | OK high (0.36)               | OK high (0.62)              |
| spatial-severity-cold-chain               | spatial_anomaly      | critical          | OK critical (1.00)          | OK critical (1.00)          | ERR moderate (0.31)          | OK critical (0.61)          |
| spatial-status-on-schedule                | spatial_anomaly      | on_schedule       | OK on_schedule (0.99)       | OK on_schedule (0.98)       | OK on_schedule (0.51)        | OK on_schedule (0.98)       |
| spatial-status-delayed-traffic            | spatial_anomaly      | delayed_explained | OK delayed_explained (1.00) | OK delayed_explained (1.00) | ERR on_schedule (0.33)       | OK delayed_explained (0.99) |
| spatial-status-unexplained                | spatial_anomaly      | investigate       | OK investigate (1.00)       | OK investigate (0.98)       | ERR delayed_explained (0.36) | OK investigate (0.93)       |
| spatial-status-corridor-exit              | spatial_anomaly      | critical          | OK critical (1.00)          | OK critical (1.00)          | OK critical (0.32)           | OK critical (0.98)          |
| security-severity-outdated-library        | security_triage      | medium            | OK medium (1.00)            | OK medium (1.00)            | OK medium (0.70)             | OK medium (0.97)            |
| security-severity-idor                    | security_triage      | high              | OK high (1.00)              | OK high (0.96)              | OK high (0.34)               | OK high (0.99)              |
| security-severity-production-key          | security_triage      | critical          | OK critical (1.00)          | ERR high (0.57)             | ERR low (0.24)               | OK critical (0.97)          |
| security-alert-login-travel               | security_triage      | contain           | OK contain (1.00)           | OK contain (0.90)           | ERR review (0.47)            | OK contain (0.75)           |
| security-alert-known-vpn                  | security_triage      | dismiss           | OK dismiss (0.86)           | OK dismiss (0.54)           | ERR review (0.43)            | OK dismiss (0.71)           |
| security-alert-review                     | security_triage      | review            | OK review (1.00)            | OK review (1.00)            | OK review (0.50)             | OK review (1.00)            |
| security-phishing-report                  | security_triage      | true              | OK true (0.95)              | OK true (1.00)              | ERR false (0.52)             | OK true (0.99)              |
| security-benign-password-reset            | security_triage      | false             | OK false (0.96)             | OK false (0.75)             | ERR true (0.52)              | OK false (1.00)             |
| security-severity-exposed-test-token      | security_triage      | low               | OK low (1.00)               | OK low (0.94)               | OK low (0.39)                | OK low (0.95)               |
| security-alert-mass-download              | security_triage      | incident          | OK incident (1.00)          | OK incident (0.95)          | ERR review (0.39)            | OK incident (0.98)          |
| thread-billing-then-delivery              | thread_routing       | orders            | OK orders (1.00)            | OK orders (1.00)            | ERR account (0.25)           | OK orders (0.93)            |
| thread-delivery-then-refund               | thread_routing       | billing           | OK billing (1.00)           | OK billing (0.95)           | ERR account (0.25)           | OK billing (0.99)           |
| thread-quoted-billing                     | thread_routing       | account           | OK account (1.00)           | OK account (0.99)           | OK account (0.25)            | OK account (0.88)           |
| thread-withdrawn                          | thread_routing       | other             | ERR orders (0.53)           | ERR orders (1.00)           | ERR account (0.25)           | ERR orders (0.93)           |
| thread-invoice-then-role                  | thread_routing       | account           | OK account (0.99)           | ERR billing (1.00)          | OK account (0.25)            | OK account (0.74)           |
| thread-login-then-return                  | thread_routing       | orders            | OK orders (1.00)            | OK orders (1.00)            | ERR account (0.25)           | OK orders (0.99)            |
| thread-sustainability-then-charge         | thread_routing       | billing           | OK billing (1.00)           | OK billing (0.96)           | ERR account (0.25)           | OK billing (0.93)           |
| thread-agent-suggests-refund              | thread_routing       | orders            | OK orders (1.00)            | OK orders (1.00)            | ERR account (0.25)           | OK orders (0.93)            |
| thread-keep-item-explain-charge           | thread_routing       | billing           | OK billing (0.99)           | OK billing (0.96)           | ERR account (0.25)           | OK billing (0.97)           |
| thread-thanks-only                        | thread_routing       | other             | OK other (0.51)             | ERR orders (1.00)           | ERR account (0.25)           | ERR orders (0.93)           |
| exception-owner-read                      | exception_scope      | true              | OK true (0.98)              | OK true (1.00)              | OK true (0.64)               | OK true (0.94)              |
| exception-owner-hold                      | exception_scope      | false             | OK false (0.96)             | OK false (0.87)             | ERR true (0.64)              | ERR true (0.56)             |
| exception-admin-hold                      | exception_scope      | false             | OK false (0.96)             | OK false (0.85)             | ERR true (0.63)              | OK false (0.62)             |
| exception-admin-read                      | exception_scope      | true              | OK true (0.98)              | OK true (1.00)              | OK true (0.62)               | OK true (0.85)              |
| exception-contractor-own                  | exception_scope      | false             | OK false (0.95)             | OK false (1.00)             | ERR true (0.59)              | OK false (0.78)             |
| exception-employee-other                  | exception_scope      | false             | OK false (0.94)             | ERR true (0.99)             | ERR true (0.64)              | OK false (0.68)             |
| exception-biography-sensitive             | exception_scope      | true              | OK true (0.98)              | OK true (1.00)              | OK true (0.64)               | OK true (0.94)              |
| exception-owner-write                     | exception_scope      | false             | OK false (0.96)             | ERR true (0.99)             | OK false (0.63)              | OK false (0.93)             |
| exception-hold-absent                     | exception_scope      | true              | OK true (0.96)              | OK true (0.99)              | OK true (0.61)               | OK true (0.90)              |
| exception-sensitivity-payroll             | exception_scope      | restricted        | OK restricted (1.00)        | OK restricted (0.99)        | ERR confidential (0.45)      | OK restricted (0.93)        |
| lookup-eu-2025                            | structured_lookup    | candidate_3       | OK candidate_3 (1.00)       | OK candidate_3 (1.00)       | ERR candidate_2 (0.34)       | OK candidate_3 (0.61)       |
| lookup-region-absent                      | structured_lookup    | none              | OK none (0.98)              | OK none (1.00)              | ERR candidate_2 (0.36)       | OK none (0.75)              |
| lookup-footnote                           | structured_lookup    | candidate_2       | OK candidate_2 (1.00)       | OK candidate_2 (0.93)       | OK candidate_2 (0.37)        | OK candidate_2 (0.99)       |
| lookup-second-invoice                     | structured_lookup    | candidate_2       | OK candidate_2 (1.00)       | OK candidate_2 (1.00)       | OK candidate_2 (0.38)        | OK candidate_2 (0.99)       |
| lookup-business-days                      | structured_lookup    | candidate_3       | OK candidate_3 (0.49)       | OK candidate_3 (0.97)       | ERR candidate_2 (0.32)       | ERR candidate_2 (0.64)      |
| lookup-kilograms                          | structured_lookup    | candidate_2       | OK candidate_2 (0.99)       | ERR none (0.87)             | ERR candidate_1 (0.37)       | OK candidate_2 (0.72)       |
| lookup-total-due                          | structured_lookup    | candidate_3       | OK candidate_3 (1.00)       | OK candidate_3 (1.00)       | ERR candidate_2 (0.33)       | OK candidate_3 (0.99)       |
| lookup-date-absent                        | structured_lookup    | none              | OK none (1.00)              | OK none (1.00)              | ERR candidate_2 (0.38)       | OK none (0.93)              |
| lookup-later-year                         | structured_lookup    | candidate_3       | OK candidate_3 (1.00)       | OK candidate_3 (1.00)       | ERR candidate_1 (0.41)       | OK candidate_3 (0.96)       |
| lookup-budget-complete                    | structured_lookup    | complete          | OK complete (1.00)          | OK complete (1.00)          | ERR partial (0.33)           | OK complete (0.99)          |
| tool-draft-valid                          | tool_selection       | true              | OK true (0.97)              | OK true (1.00)              | OK true (0.61)               | OK true (0.96)              |
| tool-draft-but-send                       | tool_selection       | false             | OK false (0.98)             | ERR true (0.95)             | ERR true (0.56)              | ERR true (0.92)             |
| tool-street-conflict                      | tool_selection       | false             | OK false (0.97)             | ERR true (0.99)             | OK false (0.66)              | ERR true (0.56)             |
| tool-optional-cc                          | tool_selection       | true              | OK true (0.69)              | OK true (1.00)              | OK true (0.62)               | OK true (0.93)              |
| tool-city-missing                         | tool_selection       | false             | OK false (0.93)             | ERR true (1.00)             | ERR true (0.52)              | ERR true (0.62)             |
| tool-wrong-name                           | tool_selection       | false             | OK false (0.98)             | ERR true (0.97)             | ERR true (0.59)              | ERR true (0.59)             |
| tool-choose-draft                         | tool_selection       | call_2            | OK call_2 (0.99)            | OK call_2 (1.00)            | ERR call_1 (0.39)            | OK call_2 (0.97)            |
| tool-none-wrong-subject                   | tool_selection       | none              | OK none (0.87)              | ERR call_2 (0.95)           | ERR call_2 (0.33)            | OK none (0.49)              |
| tool-none-two-match                       | tool_selection       | none              | ERR call_1 (0.91)           | ERR call_1 (1.00)           | ERR call_3 (0.35)            | ERR call_1 (0.74)           |
| tool-choose-with-header                   | tool_selection       | call_3            | OK call_3 (0.86)            | OK call_3 (0.99)            | ERR call_1 (0.37)            | OK call_3 (0.96)            |
| security-narrative-readme                 | narrative_security   | informational     | OK informational (1.00)     | OK informational (1.00)     | ERR low (0.45)               | OK informational (1.00)     |
| security-narrative-sandbox                | narrative_security   | low               | OK low (1.00)               | OK low (1.00)               | OK low (0.56)                | OK low (0.99)               |
| security-narrative-staging                | narrative_security   | medium            | OK medium (1.00)            | OK medium (0.97)            | OK medium (0.74)             | OK medium (0.98)            |
| security-narrative-production-key         | narrative_security   | critical          | OK critical (1.00)          | ERR low (0.55)              | OK critical (0.41)           | OK critical (0.96)          |
| security-narrative-vpn-denied             | narrative_security   | contain           | ERR review (0.63)           | ERR review (0.86)           | ERR review (0.38)            | OK contain (0.89)           |
| security-narrative-vpn-confirmed          | narrative_security   | dismiss           | ERR review (0.91)           | ERR review (0.88)           | ERR review (0.44)            | OK dismiss (0.47)           |
| security-narrative-same-country           | narrative_security   | review            | OK review (1.00)            | OK review (1.00)            | OK review (0.49)             | OK review (1.00)            |
| security-narrative-copy                   | narrative_security   | incident          | OK incident (0.97)          | OK incident (1.00)          | OK incident (0.60)           | OK incident (1.00)          |
| security-narrative-phishing               | narrative_security   | true              | OK true (0.96)              | OK true (1.00)              | ERR false (0.67)             | OK true (0.99)              |
| security-narrative-benign-reset           | narrative_security   | false             | OK false (0.94)             | OK false (0.92)             | OK false (0.50)              | OK false (0.96)             |
| linkage-id-update                         | record_linkage       | true              | OK true (0.99)              | OK true (1.00)              | ERR false (0.57)             | OK true (0.98)              |
| linkage-email-case                        | record_linkage       | true              | OK true (0.69)              | OK true (0.99)              | OK true (0.73)               | ERR false (0.50)            |
| linkage-email-name-conflict               | record_linkage       | false             | OK false (0.86)             | ERR true (0.97)             | ERR true (0.77)              | OK false (0.56)             |
| linkage-not-transitive                    | record_linkage       | false             | OK false (0.86)             | ERR true (0.91)             | OK false (0.59)              | OK false (0.59)             |
| linkage-shared-id-chain                   | record_linkage       | true              | OK true (0.97)              | OK true (0.99)              | ERR false (0.56)             | OK true (0.75)              |
| linkage-phone-format                      | record_linkage       | true              | OK true (0.93)              | OK true (0.97)              | OK true (0.62)               | OK true (0.68)              |
| linkage-name-city-only                    | record_linkage       | false             | OK false (0.95)             | ERR true (0.96)             | OK false (0.52)              | OK false (0.78)             |
| linkage-department-rename                 | record_linkage       | true              | OK true (0.99)              | OK true (1.00)              | ERR false (0.69)             | OK true (0.91)              |
| linkage-quoted-former-name                | record_linkage       | true              | OK true (0.99)              | OK true (1.00)              | ERR false (0.60)             | OK true (0.99)              |
| linkage-confidence-shared-id              | record_linkage       | high              | OK high (1.00)              | OK high (1.00)              | ERR moderate (0.30)          | OK high (0.94)              |
| orchestrate-respond-weather               | agent_orchestration  | respond           | OK respond (1.00)           | OK respond (0.50)           | OK respond (0.29)            | OK respond (0.98)           |
| orchestrate-respond-refund                | agent_orchestration  | respond           | OK respond (1.00)           | OK respond (0.90)           | OK respond (0.24)            | OK respond (0.99)           |
| orchestrate-ask-recipient                 | agent_orchestration  | ask               | OK ask (1.00)               | OK ask (0.99)               | ERR wait (0.23)              | ERR act (0.52)              |
| orchestrate-ask-destination               | agent_orchestration  | ask               | OK ask (1.00)               | OK ask (0.98)               | OK ask (0.22)                | ERR act (0.53)              |
| orchestrate-handoff-billing               | agent_orchestration  | handoff           | OK handoff (1.00)           | OK handoff (0.99)           | ERR wait (0.23)              | OK handoff (0.82)           |
| orchestrate-handoff-writer                | agent_orchestration  | handoff           | OK handoff (1.00)           | OK handoff (0.95)           | ERR act (0.27)               | ERR act (0.85)              |
| orchestrate-wait-running                  | agent_orchestration  | wait              | OK wait (1.00)              | OK wait (0.71)              | OK wait (0.25)               | ERR act (0.91)              |
| orchestrate-wait-failed                   | agent_orchestration  | wait              | OK wait (1.00)              | ERR ask (0.57)              | ERR act (0.24)               | ERR act (0.71)              |
| orchestrate-act-lookup                    | agent_orchestration  | act               | OK act (1.00)               | OK act (0.97)               | OK act (0.25)                | OK act (0.96)               |
| orchestrate-act-after-failure             | agent_orchestration  | act               | OK act (1.00)               | OK act (0.98)               | OK act (0.26)                | OK act (0.97)               |

## Method

Fixture/artifact provenance hash: `b98cf179b1d8b9ece8886845d959a42330255d140ca87671f7c2af00b9b9b083`.
All metrics are derived from supplied raw JSON artifacts. Score MAE uses the normalized probability-weighted ordinal score. Latency is not hardware-equivalent across hosted and local backends.
