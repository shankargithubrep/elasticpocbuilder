# MME Service Request Alert Demo Scenarios

This document describes 5 realistic failure scenarios that can be injected into the data stream for customer demonstrations. Each scenario is designed to trigger the watcher alert and showcase different types of network issues.

---

## Scenario 1: Mass Authentication Failure Event

### Overview
Simulates HSS (Home Subscriber Server) database corruption or synchronization issues affecting subscriber authentication.

### Technical Details
- **Primary CFCQ Code:** `2 IMSI unknown in HSS`
- **Secondary Codes:** `3 Illegal MS`, `5 IMEI not accepted`
- **Affected IMSIs:** 500+ unique subscribers
- **Affected Hosts:** 2-3 MME hosts in same region
- **Duration:** 10-15 minute spike
- **Pattern:** High IMSI diversity, normal cell distribution

### Watcher Trigger Conditions
- `imsi_change_1` > 400 (spike in unique IMSI count)
- `imsi_change_2` > 280 (sustained over 2 intervals)
- `cell_spike` values remain normal
- Minimum 200 failures per 5-minute interval

### Business Impact Talking Points
- **Customer Experience:** Subscribers unable to make calls or access data services
- **Geographic Impact:** Could affect entire region or subscriber segment
- **Revenue Impact:** Direct service downtime leads to revenue loss
- **SLA Risk:** Potential SLA violations with enterprise customers
- **Churn Risk:** Extended outages increase customer churn probability
- **Root Cause:** Database corruption, failed HSS update, sync issues between redundant HSS nodes

### Demo Value
Demonstrates how the watcher detects unusual subscriber authentication patterns before help desk is overwhelmed. Shows value of proactive alerting vs. reactive ticket management.

---

## Scenario 2: Cell Tower Handoff Cascade Failure

### Overview
Simulates radio equipment failure, backhaul network issues, or cell site power failure affecting handoffs.

### Technical Details
- **Primary CFCQ Code:** `15 No Suitable Cells In tracking area`
- **Secondary Codes:** `12 Tracking Area not allowed`, `35 Requested service option not authorized in this PLMN`
- **Affected Cells:** >50 unique cell IDs with high churn rate
- **Affected Hosts:** Specific geographic MME hosts (e.g., mme-west-03, mme-west-04)
- **Duration:** Sustained 15-20 minutes
- **Pattern:** High cell ID diversity, relatively stable IMSI population

### Watcher Trigger Conditions
- `cell_id_change_1` > 50 (spike in unique cell count)
- `cell_id_change_2` > 25 (sustained pattern)
- Both `cell_spike_1` >= 1 AND `cell_spike_2` >= 1
- Indicates systematic handoff failures

### Business Impact Talking Points
- **Customer Experience:** Dropped calls during mobility, interrupted data sessions
- **Network Health:** Physical infrastructure problem (tower, fiber cut, microwave link)
- **Quality Metrics:** QoS degradation visible in customer experience metrics
- **Regulatory Risk:** Potential FCC complaints about coverage gaps
- **Operational Response:** Requires immediate field technician dispatch
- **Root Cause:** Cell site power failure, backhaul circuit down, antenna/radio failure

### Demo Value
Showcases the dual-lag cell ID spike detection that identifies systematic infrastructure failures. Illustrates how pattern analysis catches issues that simple error counting would miss.

---

## Scenario 3: Security/Roaming Attack or Misconfiguration

### Overview
Simulates rogue network attempts, SS7 attacks, or international roaming configuration errors.

### Technical Details
- **Primary CFCQ Code:** `11 PLMN not allowed`, `13 Roaming not allowed in this tracking area`
- **Secondary Codes:** `7 EPS services not allowed`, `14 EPS services not allowed in this PLMN`
- **Affected IMSIs:** Sudden influx of new IMSIs (>280 in 2-interval lag)
- **Affected Hosts:** Border region or international gateway MME hosts
- **Duration:** 10-30 minutes (attack duration or until config fixed)
- **Pattern:** Very high IMSI diversity, moderate cell diversity

### Watcher Trigger Conditions
- `imsi_change_2` > 280 (unusual population change over 2 lags)
- High unique IMSI cardinality
- Pattern suggests new subscriber population attempting access
- Serial diff algorithm detects anomalous IMSI influx

### Business Impact Talking Points
- **Security Threat:** Potential SS7 attack, fake base station, or rogue network
- **Roaming Issues:** Partner misconfiguration blocking legitimate international travelers
- **Customer Impact:** International travelers unable to access network services
- **Revenue Leakage:** Billing discrepancies if roaming agreements misconfigured
- **Compliance Risk:** Regulatory issues with lawful intercept or emergency services
- **Root Cause:** Roaming partner config error, security attack, policy update failure

### Demo Value
Highlights the sophisticated serial diff analysis that detects unusual subscriber population changes invisible to traditional error rate monitoring. Shows security and compliance use cases.

---

## Scenario 4: MME Software Bug or Resource Exhaustion

### Overview
Simulates memory leak, CPU exhaustion, software defect, or capacity overload on specific MME nodes.

### Technical Details
- **Primary CFCQ Code:** `22 Congestion`, `17 Network failure`
- **Secondary Codes:** `42 Severe network failure`, `40 No EPS bearer context activated`
- **Affected Hosts:** 1-2 specific MME hosts (platform issue, not network-wide)
- **Duration:** Gradual build-up over 20-30 minutes
- **Pattern:** Both IMSI and Cell ID metrics show sustained spikes
- **Volume:** Minimum 200 failures per 5-minute interval (bucket_selector threshold)

### Watcher Trigger Conditions
- All four spike conditions must be met simultaneously:
  - `imsi_spike_1` >= 1
  - `imsi_spike_2` >= 1
  - `cell_spike_1` >= 1
  - `cell_spike_2` >= 1
- Multi-dimensional problem (not isolated to one metric)
- Sustained across multiple lag periods

### Business Impact Talking Points
- **Operational Action:** Immediate MME restart or failover required
- **Blast Radius:** All subscribers currently served by specific MME affected
- **Escalation Risk:** Could escalate to complete MME failure if ignored
- **Proactive Value:** Detection before total outage prevents larger incident
- **Capacity Planning:** Insight for scaling or optimization needs
- **Root Cause:** Software bug, memory leak, database connection pool exhaustion, traffic overload

### Demo Value
Demonstrates the stringent multi-condition logic (all 4 spike conditions) that filters noise and only alerts on serious, multi-dimensional problems. Shows how the watcher prevents false positives.

---

## Scenario 5: Core Network Split-Brain or Signaling Storm

### Overview
Simulates S1 interface issues, GTP-C protocol failures, DNS/routing problems, or distributed system partitioning.

### Technical Details
- **Primary CFCQ Code:** `18 CS domain not available`, `39 CS service temporarily not available`
- **Secondary Codes:** `19 ESM failure`, `17 Network failure`
- **Affected Hosts:** Multiple MME hosts simultaneously (3-5 hosts)
- **Duration:** Cyclical pattern - fails, recovers, fails (5-min cycles)
- **Pattern:** Both high IMSI churn AND high cell ID churn across multiple hosts

### Watcher Trigger Conditions
- Multiple hosts exhibit the spike pattern simultaneously
- `final_host_filter` bucket_selector catches multi-host failures
- Both IMSI and cell metrics spiking (systemic issue)
- Rhythmic failure pattern indicates protocol/timing issue

### Business Impact Talking Points
- **Scope:** Core network infrastructure issue, not isolated radio/cell problem
- **Service Impact:** Voice calls failing while data works (or vice versa)
- **Geographic Blast Radius:** Multiple regions impacted simultaneously
- **Root Cause Indicator:** Likely post-maintenance misconfiguration
- **Escalation:** Major incident requiring Network Operations Center escalation
- **Cross-functional:** Requires core network team, not just RAN operations
- **Root Cause:** S1 interface misconfiguration, GTP-C tunnel failures, DNS issues, NTP clock skew

### Demo Value
Showcases the aggregation-level filtering (`final_host_filter`) that distinguishes isolated incidents from systemic failures. Demonstrates enterprise-grade alerting that prevents alert fatigue.

---

## Using Scenarios in Demos

### Scenario Injection via CLI
```bash
# Inject Mass Authentication Failure
python mme_data_generator.py --scenario mass-auth-failure --scenario-duration 15

# Inject Cell Tower Cascade Failure
python mme_data_generator.py --scenario cell-handoff-failure --scenario-duration 20

# Inject Security/Roaming Attack
python mme_data_generator.py --scenario roaming-attack --scenario-duration 30

# Inject MME Resource Exhaustion
python mme_data_generator.py --scenario mme-exhaustion --scenario-duration 25

# Inject Core Network Split-Brain
python mme_data_generator.py --scenario core-network-failure --scenario-duration 30
```

### Demo Flow Recommendations

#### Option 1: Progressive Severity Demo (20 minutes)
1. **Baseline (5 min):** Normal operations at 10% failure rate - show green dashboard
2. **Scenario 1 (5 min):** Mass auth failure - demonstrate first alert trigger
3. **Investigation (3 min):** Drill down into IMSI patterns, show root cause analysis
4. **Scenario 4 (5 min):** MME exhaustion - show gradual degradation detection
5. **Value Proposition (2 min):** "Caught this 15 minutes before customer calls spiked"

#### Option 2: Security & Compliance Focus (15 minutes)
1. **Baseline (3 min):** Normal operations
2. **Scenario 3 (7 min):** Roaming attack - emphasize security detection
3. **Compliance Discussion (5 min):** Regulatory requirements, audit trail, forensics

#### Option 3: Multi-Host Incident (10 minutes)
1. **Baseline (2 min):** Normal operations
2. **Scenario 5 (5 min):** Core network failure across multiple hosts
3. **Ops Response (3 min):** Show how alert leads to faster MTTR

### Visualization Talking Points

When demoing each scenario, highlight:

1. **Time Series Graphs:** Show spike in unique IMSI/Cell counts over 5-min intervals
2. **Serial Diff Metrics:** Demonstrate lag-1 and lag-2 change detection
3. **Bucket Selector Logic:** Explain how 200-doc threshold filters partial buckets
4. **Multi-Host Aggregation:** Show which MME hosts are affected
5. **Alert Payload:** Display the actual watcher output structure

### Technical Deep Dive Points

For technical audiences, explain:

1. **Why Serial Diff?** Detects rate-of-change, not absolute values
2. **Why Two Lags?** Confirms sustained pattern, not transient blip
3. **Why 200 Doc Threshold?** Filters incomplete data from 5-min window edges
4. **Why All 4 Spikes?** Prevents false positives from single-metric anomalies
5. **Why Bucket Selector?** Ensures only problematic hosts appear in results

---

## Scenario Comparison Matrix

| Scenario | Primary Metric | Duration | Hosts Affected | Detection Time | MTTR Impact |
|----------|---------------|----------|----------------|----------------|-------------|
| Mass Auth Failure | IMSI spike | 10-15 min | 2-3 | ~5 min | -40% |
| Cell Handoff Failure | Cell ID spike | 15-20 min | 2-4 | ~5 min | -35% |
| Roaming Attack | IMSI population change | 10-30 min | 1-2 | ~10 min | -50% |
| MME Exhaustion | Both IMSI & Cell | 20-30 min | 1-2 | ~10 min | -60% |
| Core Network Failure | Multi-host, both metrics | Cyclical | 3-5 | ~5 min | -45% |

*MTTR Impact: Estimated reduction in Mean Time To Resolution with proactive alerting*

---

## Customizing Scenarios

To adjust scenario parameters, modify these settings in the data generator:

- **Failure intensity:** Adjust percentage of failures during scenario window
- **Host concentration:** Limit failures to specific MME hosts
- **IMSI diversity:** Control how many unique IMSIs are affected
- **Cell diversity:** Control cell ID churn rate
- **Duration:** Scenario injection time window
- **Pattern:** Gradual build-up vs. sudden spike

See the data generator code for implementation details.
