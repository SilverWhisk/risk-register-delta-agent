# 📋 Risk Register Delta Agent

An AI-powered agent that compares a current trial data snapshot against an approved risk register, identifies what has changed and why, and generates a structured delta report — so the quarterly risk review starts with a pre-reasoned baseline instead of a blank page.

**Live Demo:** [risk-register-delta-agent-2026.streamlit.app](https://risk-register-delta-agent-2026.streamlit.app)

---

## The Problem

Maintaining a risk register is supposed to be an ongoing process. In practice, it's often a meeting — the CTM calls a quarterly Risk Register Review, pulls together the study team, and the group works through what has changed since the last approved version. CTMs, CRAs, data managers, medical monitors, and safety leads all weigh in.

The problem is preparation. By the time the meeting happens, the team is working from memory, scattered monitoring reports, and a risk register that hasn't been touched in weeks. The first hour is spent reconstructing what actually happened — before the real discussion about what it means for risk can begin.

This agent was inspired by a real request from a global biopharmaceutical company: automate the delta analysis so the review meeting starts with a pre-reasoned report. The team's expertise goes toward challenging and validating the output — not building it from scratch. What used to take a two-hour meeting that still didn't happen on time can now begin in minutes.

---

## What It Does

### Core Workflow

1. **Ingests** two required documents plus one optional historical reference:
   - Approved Risk Register — the last signed-off version (the baseline)
   - Trial Data Snapshot — current enrollment metrics, safety events, protocol deviations, and site performance data since the last review
   - *(Optional)* Master Risk Register — the sponsor or CRO's historical risk library, capturing risks identified and mitigated across prior studies

2. **Compares** the snapshot against each risk in the approved register and determines:
   - **Escalated** — risk has increased in likelihood, impact, or severity
   - **De-escalated** — risk has decreased or mitigation is working
   - **Closed** — risk is fully resolved and no longer active
   - **No Change** — status unchanged
   - **New** — risk evidenced by the snapshot but not in the approved register

3. **Explains why** each change occurred — citing specific events, data points, and trends from the snapshot, not just asserting that something changed

4. **Benchmarks against history** when a Master Risk Register is provided — flagging which changes match historical precedents, applying proven mitigations, and surfacing regulatory history (FDA 483s, clinical holds) for similar risk patterns

5. **Presents each change** for individual human accept/reject review — with reviewer name, role, and timestamp recorded for every decision

6. **Calculates** an updated overall study risk score and direction of travel (increased/decreased/stable) compared to the previous approved version

7. **Exports** a final report in JSON (for RBQM system import) and formatted PDF (for TMF filing)

---

## Key Features

### Per-Risk Accept/Reject Review
Every proposed change is presented individually — the reviewer accepts or rejects each one, with their name, role, and timestamp recorded inline. No all-or-nothing approval. This mirrors how a real risk register review works and ensures the human remains accountable for every decision.

### Reviewer Identity & Audit Trail
Each decision is stamped with the reviewer's name, role, and date. The complete audit trail is included in both the JSON and PDF exports — providing a regulatory-grade record of who reviewed what and when.

> **MVP Note:** In this demo, reviewer identity is self-declared. In a production deployment, reviewers would authenticate via SSO (e.g. Okta or Microsoft Entra ID), eliminating impersonation risk and ensuring a tamper-evident, regulatory-grade audit trail that meets 21 CFR Part 11 requirements.

### Dual Export Format
- **JSON** — structured for direct import into RBQM systems or risk register tools to apply accepted changes
- **PDF** — formatted clinical report for TMF filing and study team distribution, using a clean clinical brand design

### Risk Score Direction
The agent calculates both the previous and updated overall study risk score, with a narrative explaining the score movement. Useful for portfolio-level reporting — comparing risk trajectory across studies over time.

---


## Business Value

A risk register that is not maintained is a compliance liability. In practice, risk registers fall behind because the update process is manual, time-consuming, and dependent on a meeting that is hard to schedule. This agent makes maintenance effortless — turning a two-hour team exercise into a 20-minute review.

**Time Savings**

The quarterly risk register review requires the CTM to pull together the study team, reconstruct what has changed from scattered monitoring reports, work through each risk collaboratively, and document decisions. This typically consumes two to four hours of meeting time plus two to three hours of preparation per cycle.

At a quarterly cadence over a typical Phase 2 study, that represents 6–8 full review cycles — consuming 24–56 hours of cross-functional team time on risk register maintenance alone.

**Estimated time saving per study: 20–45 hours over the study lifecycle.**

**Cost Efficiency**

At a blended rate of $300–$600 per hour, traditional risk register maintenance across a Phase 2 study costs $7,200–$33,600 in direct labor. This excludes the hidden cost of delayed reviews — risk registers kept in Excel shadow systems outside the validated RBQM tool, or reviews that simply don't happen on schedule.

**Estimated cost saving per study: $7,000–$33,000. Across a portfolio of 10 active studies, savings compound significantly.**

**Compliance and Audit Readiness**

A risk register that falls behind reality is a regulatory exposure. FDA inspectors review risk management documentation as part of GCP inspections. Gaps between the documented register and actual study conduct are inspection findings.

This agent produces a complete, timestamped audit trail of every review decision — who reviewed which proposed change, whether they accepted or rejected it, and when. Every quarterly review produces a compliance-ready record designed for TMF filing and RBQM system import.

**Early Risk Detection**

An agent that can be run at any cadence — monthly, after a significant safety event, or before a DSMB meeting — catches issues when they emerge rather than when the meeting finally happens. In the demo, the agent identifies a Critical hepatic escalation, a first pancreatitis case, and two new risks not on the register — including undisclosed CYP3A4-interacting medications across multiple participants.

**Earlier detection means earlier mitigation.**

**Historical Data as a Competitive Advantage**

Sponsors that use the Master Risk Register get compounding value over time. Risk patterns that recur across studies are automatically recognized. Mitigations that worked are automatically applied. For sponsors managing portfolios of 10, 20, or 50 active studies, this institutional memory layer is the difference between repeating the same risk failures and systematically eliminating them.

**RBQM Integration Value**

The JSON export is structured for direct import into RBQM systems — accepted changes can be pushed to the risk register tool without manual re-entry. In a production deployment with direct API integration, the entire process runs as a single workflow. Manual touchpoints are reduced to the human review decisions — exactly where human judgment should be applied.

### ROI at a Glance
- ⏱ **20–45 hours** of cross-functional team time saved per study lifecycle
- 💰 **$7,000–$33,000** in direct labor cost saved per study
- 📋 Quarterly review time reduced from **2–4 hours to 20 minutes**
- 🛡 Audit-ready TMF documentation produced automatically at every review cycle
- 🔍 Risk escalations detected at any cadence — not just when the meeting happens
- 📥 JSON export structured for direct RBQM system import — no manual re-entry
- 📚 Compounding portfolio value as Master Risk Register grows over time

---
## Agentic Patterns Demonstrated

| Pattern | Implementation |
|---|---|
| **State comparison over time** | Previous register vs. current snapshot — two-snapshot reasoning |
| **Causal reasoning** | Explains *why* each risk changed, citing specific data points |
| **Autonomous classification** | Escalated / De-escalated / Closed / No Change / New |
| **Ownership assignment** | Recommended action and owner assigned per risk domain |
| **Granular human-in-the-loop** | Accept/reject per risk — not all-or-nothing |
| **Reviewer attribution** | Every decision stamped with name, role, and timestamp |
| **Audit trail generation** | Full decision log included in both export formats |
| **Historical benchmarking** | Optional fourth document enables institutional memory layer |
| **Streaming** | Real-time token streaming for large document processing |
| **State persistence** | Session state maintains results and decisions across interactions |

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.11 | Core language |
| Anthropic SDK | Claude claude-sonnet-4-5 via streaming API |
| Streamlit | Web UI, file upload, and interactive review |
| ReportLab | Formatted PDF report generation |
| pdfplumber | PDF text extraction |

---

## Project Structure

```
risk-register-delta-agent/
├── app.py                            # Streamlit UI and review workflow
├── agent.py                          # Core agent logic and CLI runner
├── prompts.py                        # System prompt and user prompt builder
├── pdf_report.py                     # PDF report generator
├── requirements.txt                  # Python dependencies
├── documents/                        # Sample documents for testing
│   ├── mock_previous_risk_register.md
│   ├── mock_trial_data_snapshot.md
│   └── mock_master_risk_register.md
└── outputs/                          # Generated reports (gitignored)
```

---

## Running Locally

### Prerequisites
- Python 3.11+
- Anthropic API key ([console.anthropic.com](https://console.anthropic.com))

### Setup

```bash
# Clone the repo
git clone https://github.com/SilverWhisk/risk-register-delta-agent.git
cd risk-register-delta-agent

# Install dependencies
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY="your-key-here"

# Run the Streamlit app
streamlit run app.py
```

### CLI Usage

```bash
# Run via command line with default mock documents
python agent.py
```

---

## Sample Documents

Three mock documents are included for testing, continuing the fictional Velaglipron Phase 2 obesity study from the companion Protocol Risk Assessment Agent:

- **mock_previous_risk_register.md** — Last approved risk register (Version 2.0, February 2025) with 10 active risks across all domains
- **mock_trial_data_snapshot.md** — Q2 2025 trial data snapshot covering the subsequent 3-month period, including a hepatic SAE, confirmed pancreatitis case, confirmed pregnancy, site performance issues, and enrollment progress
- **mock_master_risk_register.md** — Historical risk library with 16 risks across 4 domains from prior fictional studies

**The delta the agent detects in the demo:**

| Risk | Change | Trigger |
|---|---|---|
| RSK-001 (DILI) | Escalate to Critical | ALT SAE at 6.8x ULN; FDA report filed |
| RSK-003 (Pancreatitis) | Escalate to Critical | First confirmed case; was Low likelihood |
| RSK-004 (Enrollment) | De-escalate to Medium | Now at 79%, ahead of projections |
| RSK-006 (AE underreporting) | Escalate to High | Mitigation failing at Sites 04 and 14 |
| RSK-002 (Lab mismatch) | Close | Central lab fully compliant |
| RSK-008 (Pregnancy) | Escalate | First confirmed pregnancy |
| NEW | Site 14 performance | Multi-deviation pattern — not on register |
| NEW | CYP3A4 concomitant meds | Undisclosed interacting medications — not on register |

---

## Sample Output

```
📊 DELTA SUMMARY
   🔴 Escalated:     4
   🟢 De-escalated:  1
   ✅ Closed:        2
   ⚪ No Change:     1
   🆕 New Risks:     2

🎯 OVERALL STUDY RISK SCORE
   Previous Score:  62/100
   Updated Score:   81/100  📈 INCREASED

   Study risk has materially increased since the February review,
   driven by two new SAEs (hepatic and pancreatitis), a confirmed
   pregnancy, and continued AE underreporting at two sites despite
   prior mitigation. Immediate action required before next DSMB review.
```

---

## Production Considerations

This MVP demonstrates the core agentic workflow. A production deployment would additionally require:

**Validation & Accuracy**
- Labeled evaluation dataset with known risk deltas for precision/recall measurement
- Clinical risk manager review cycles for output validation
- Multi-run consistency testing across varied document inputs

**Observability**
- LLM observability tooling (e.g. Arize Phoenix) for prompt tracing, output monitoring, and drift detection
- Every agent decision logged with input/output pairs for audit purposes

**User Authentication & Audit Logging**
- Authenticated access only — no anonymous or self-declared identity; integrated with sponsor SSO (e.g. Okta or Microsoft Entra ID)
- Role-based permissions scoped to study assignment — users cannot access risk registers outside their authorized trials
- Immutable audit log capturing every submission, review decision, and export with verified user identity and timestamp
- Tamper-evident record storage meeting 21 CFR Part 11 electronic records requirements
- In this MVP, reviewer identity is self-declared — production would replace this with verified SSO authentication

**Regulatory Compliance**
- 21 CFR Part 11 compliant audit trail for all human review decisions
- System validation documentation (IQ/OQ/PQ) per GAMP 5 guidelines
- Validated JSON export schema for direct RBQM system import
- PDF output format validated for TMF filing requirements

**Infrastructure**
- Direct API integration with sponsor CTMS or EDC for real-time trial data ingestion — replacing manual snapshot upload
- Direct integration with RBQM system to push accepted changes automatically
- Multi-user concurrent review support
- Version control for prompt changes (prompt versioning affects output reliability)

---

## About

Built as part of a clinical AI portfolio demonstrating agentic AI patterns for regulated clinical development environments.

The workflow was inspired by a real request from a global biopharmaceutical company — specifically the challenge of keeping risk registers current between reviews, and the manual effort required to prepare a meaningful delta analysis before each quarterly meeting.

This agent is designed as a companion to the [Protocol Risk Assessment Agent](https://github.com/SilverWhisk/protocol-risk-assessment-agent) — which handles initial risk assessment generation at study startup. Together they address the full risk management lifecycle: initial RA generation and ongoing RA maintenance.

---

## Disclaimer

This tool is for research and demonstration purposes only. All outputs require review by a qualified clinical risk manager before use in regulated environments. Accepted changes must be validated before updating the study risk register. This agent does not constitute medical, regulatory, or legal advice.
