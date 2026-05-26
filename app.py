import streamlit as st
import anthropic
import json
from datetime import date
from prompts import SYSTEM_PROMPT, build_user_prompt
from pdf_report import generate_pdf

# Initialize session state
if "report" not in st.session_state:
    st.session_state.report = None
if "accepted" not in st.session_state:
    st.session_state.accepted = {}
if "rejected" not in st.session_state:
    st.session_state.rejected = {}
if "reviewer_signatures" not in st.session_state:
    st.session_state.reviewer_signatures = {}
if "run_history" not in st.session_state:
    st.session_state.run_history = []

# Page config
st.set_page_config(
    page_title="Risk Register Delta Agent",
    page_icon="📋",
    layout="wide"
)

# Header
st.title("📋 Risk Register Delta Agent")
st.markdown("""
Upload your approved risk register and a current trial data snapshot.
The agent identifies what has changed, why it changed, and what action
is needed — so your quarterly review starts with a pre-reasoned delta
instead of a blank page.
""")
st.divider()

# ── REVIEWER IDENTITY ─────────────────────────────────────────
st.subheader("👤 Reviewer Identity")
st.caption(
    "Required for audit trail and TMF filing. All accept/reject decisions "
    "will be logged with your name and role. "
    "⚠️ MVP note: Identity is self-declared in this demo. In a production "
    "deployment, reviewers would authenticate via SSO (e.g. Okta or Microsoft "
    "Entra ID) — eliminating impersonation risk and ensuring a tamper-evident, "
    "regulatory-grade audit trail."
)
rev_col1, rev_col2 = st.columns(2)
with rev_col1:
    reviewer_name = st.text_input(
        "Reviewer Name",
        placeholder="e.g. Dr. Sarah Chen",
        help="Your full name as it should appear in the audit trail"
    )
with rev_col2:
    reviewer_role = st.text_input(
        "Role / Title",
        placeholder="e.g. Medical Monitor",
        help="Your role on the study team"
    )
st.divider()

# ── FILE UPLOADERS ────────────────────────────────────────────
st.subheader("📄 Required Documents")
col1, col2 = st.columns(2)
with col1:
    prev_rr_file = st.file_uploader(
        "Approved Risk Register (last version)",
        type=["txt", "md", "pdf"],
        help="The most recently approved risk register version"
    )
with col2:
    snapshot_file = st.file_uploader(
        "Current Trial Data Snapshot",
        type=["txt", "md", "pdf"],
        help="Current enrollment, safety events, deviations, and site performance data"
    )

st.divider()
st.subheader("📚 Optional: Historical Reference")
col_mrr, col_info = st.columns([1, 2])
with col_mrr:
    mrr_file = st.file_uploader(
        "Master Risk Register",
        type=["txt", "md", "pdf"],
        help="Historical risk library for institutional benchmarking"
    )
with col_info:
    if mrr_file:
        st.success(
            "✅ Master Risk Register uploaded — agent will benchmark "
            "changes against historical precedents."
        )
    else:
        st.info(
            "💡 Upload your Master Risk Register to enable "
            "historical benchmarking of risk changes."
        )

def read_uploaded_file(f):
    return f.read().decode("utf-8")

def run_delta_analysis(prev_text, snapshot_text, mrr_text=None):
    client = anthropic.Anthropic()
    raw_output = ""
    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": build_user_prompt(prev_text, snapshot_text, mrr_text)
            }
        ]
    ) as stream:
        for text in stream.text_stream:
            raw_output += text
    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        clean = raw_output.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)

def display_report(report):
    """Render the delta report in Streamlit."""
    meta    = report.get("report_metadata", {})
    summary = report.get("delta_summary", {})
    deltas  = report.get("risk_deltas", [])
    new     = report.get("new_risks", [])
    overall = report.get("overall_assessment", {})

    # Metadata
    st.subheader("📋 Report Summary")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Study",          meta.get("drug_name", "N/A"))
    col2.metric("Study ID",       meta.get("study_id", "N/A"))
    col3.metric("Snapshot Date",  meta.get("snapshot_date", "N/A"))
    col4.metric("Risks Reviewed", meta.get("total_risks_reviewed", 0))
    st.divider()

    # Overall score
    prev_score    = overall.get("previous_study_risk_score", 0)
    updated_score = overall.get("updated_study_risk_score", 0)
    direction     = overall.get("score_direction", "STABLE")
    arrow = {"INCREASED": "📈", "DECREASED": "📉", "STABLE": "➡️"}.get(direction, "")

    st.subheader("🎯 Overall Study Risk Score")
    sc1, sc2, sc3 = st.columns(3)
    sc1.metric("Previous Score", f"{prev_score}/100")
    sc2.metric("Updated Score",  f"{updated_score}/100",
               delta=f"{updated_score - prev_score:+d}")
    sc3.metric("Direction", f"{arrow} {direction}")
    st.info(overall.get("narrative", ""))
    st.divider()

    # Delta summary metrics
    st.subheader("📊 Delta Summary")
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("🔴 Escalated",    summary.get("escalated", 0))
    m2.metric("🟢 De-escalated", summary.get("de_escalated", 0))
    m3.metric("✅ Closed",       summary.get("closed", 0))
    m4.metric("⚪ No Change",    summary.get("no_change", 0))
    m5.metric("🆕 New Risks",    summary.get("new_risks", 0))
    st.divider()

    # Reviewer identity reminder
    if not reviewer_name:
        st.warning("⚠️ Please enter your name and role above before reviewing changes — required for audit trail.")

    # Risk deltas — changes only
    changed = [d for d in deltas if d.get("delta_type") != "NO CHANGE"]
    if changed:
        st.subheader(f"🔄 Risk Changes ({len(changed)} changes)")
        st.caption("Review each proposed change and accept or reject individually. Your decision will be logged with your name and role.")

        for delta in changed:
            icon = {"ESCALATED": "🔴", "DE-ESCALATED": "🟢",
                    "CLOSED": "✅"}.get(delta.get("delta_type"), "⚪")
            rid = delta.get("risk_id")

            with st.expander(
                f"{icon} {rid} | {delta.get('risk_title')} | "
                f"{delta.get('previous_rating')} → {delta.get('recommended_rating')} "
                f"({delta.get('delta_type')})"
            ):
                col1, col2, col3 = st.columns(3)
                col1.markdown(f"**Previous Rating:** {delta.get('previous_rating')}")
                col2.markdown(f"**Recommended Rating:** {delta.get('recommended_rating')}")
                col3.markdown(f"**Urgency:** {delta.get('urgency')}")
                st.markdown(f"**Why it changed:** {delta.get('reason')}")
                st.markdown(f"**Supporting data:** {delta.get('supporting_data')}")
                st.markdown(f"**Recommended action:** {delta.get('recommended_action')}")
                st.markdown(f"**Owner:** {delta.get('owner')}")
                if delta.get("historically_precedented"):
                    st.warning(f"📚 Historically precedented — Register ID: {delta.get('matched_register_id')}")

                # Accept/reject with reviewer signature
                st.markdown("---")
                col_a, col_r, col_sig = st.columns([1, 1, 2])
                with col_a:
                    if st.button("✅ Accept", key=f"accept_{rid}",
                                 use_container_width=True, type="primary"):
                        if not reviewer_name:
                            st.error("Enter reviewer name above first.")
                        else:
                            signed = dict(delta)
                            signed["reviewer_name"] = reviewer_name
                            signed["reviewer_role"] = reviewer_role
                            signed["review_timestamp"] = str(date.today())
                            st.session_state.accepted[rid] = signed
                            st.session_state.rejected.pop(rid, None)
                with col_r:
                    if st.button("❌ Reject", key=f"reject_{rid}",
                                 use_container_width=True):
                        if not reviewer_name:
                            st.error("Enter reviewer name above first.")
                        else:
                            signed = dict(delta)
                            signed["reviewer_name"] = reviewer_name
                            signed["reviewer_role"] = reviewer_role
                            signed["review_timestamp"] = str(date.today())
                            st.session_state.rejected[rid] = signed
                            st.session_state.accepted.pop(rid, None)
                with col_sig:
                    if rid in st.session_state.accepted:
                        d = st.session_state.accepted[rid]
                        st.success(f"✅ Accepted by {d.get('reviewer_name')} ({d.get('reviewer_role')}) on {d.get('review_timestamp')}")
                    elif rid in st.session_state.rejected:
                        d = st.session_state.rejected[rid]
                        st.error(f"❌ Rejected by {d.get('reviewer_name')} ({d.get('reviewer_role')}) on {d.get('review_timestamp')}")
                    else:
                        st.caption("⏳ Pending review")

        st.divider()

    # New risks
    if new:
        st.subheader(f"🆕 New Risks ({len(new)} identified)")
        st.caption("These risks were not in the approved register.")

        for risk in new:
            rid = risk.get("risk_id")
            with st.expander(
                f"🆕 {rid} | {risk.get('risk_title')} | "
                f"Recommended: {risk.get('recommended_rating')}"
            ):
                col1, col2 = st.columns(2)
                col1.markdown(f"**Domain:** {risk.get('domain')}")
                col2.markdown(f"**Urgency:** {risk.get('urgency')}")
                st.markdown(f"**Description:** {risk.get('description')}")
                st.markdown(f"**Supporting data:** {risk.get('supporting_data')}")
                st.markdown(f"**Recommended action:** {risk.get('recommended_action')}")
                st.markdown(f"**Owner:** {risk.get('owner')}")
                if risk.get("historically_precedented"):
                    st.warning(f"📚 Historically precedented — Register ID: {risk.get('matched_register_id')}")

                st.markdown("---")
                col_a, col_r, col_sig = st.columns([1, 1, 2])
                with col_a:
                    if st.button("✅ Accept", key=f"accept_{rid}",
                                 use_container_width=True, type="primary"):
                        if not reviewer_name:
                            st.error("Enter reviewer name above first.")
                        else:
                            signed = dict(risk)
                            signed["reviewer_name"] = reviewer_name
                            signed["reviewer_role"] = reviewer_role
                            signed["review_timestamp"] = str(date.today())
                            st.session_state.accepted[rid] = signed
                            st.session_state.rejected.pop(rid, None)
                with col_r:
                    if st.button("❌ Reject", key=f"reject_{rid}",
                                 use_container_width=True):
                        if not reviewer_name:
                            st.error("Enter reviewer name above first.")
                        else:
                            signed = dict(risk)
                            signed["reviewer_name"] = reviewer_name
                            signed["reviewer_role"] = reviewer_role
                            signed["review_timestamp"] = str(date.today())
                            st.session_state.rejected[rid] = signed
                            st.session_state.accepted.pop(rid, None)
                with col_sig:
                    if rid in st.session_state.accepted:
                        d = st.session_state.accepted[rid]
                        st.success(f"✅ Accepted by {d.get('reviewer_name')} ({d.get('reviewer_role')}) on {d.get('review_timestamp')}")
                    elif rid in st.session_state.rejected:
                        d = st.session_state.rejected[rid]
                        st.error(f"❌ Rejected by {d.get('reviewer_name')} ({d.get('reviewer_role')}) on {d.get('review_timestamp')}")
                    else:
                        st.caption("⏳ Pending review")

        st.divider()

    # Unchanged risks
    unchanged = [d for d in deltas if d.get("delta_type") == "NO CHANGE"]
    if unchanged:
        with st.expander(f"⚪ Unchanged Risks ({len(unchanged)} — no action required)"):
            for r in unchanged:
                st.markdown(
                    f"**{r.get('risk_id')}** | {r.get('risk_title')} | "
                    f"{r.get('recommended_rating')}"
                )

def build_final_report(report):
    """Build final report with audit trail from session state."""
    accepted = st.session_state.accepted
    rejected = st.session_state.rejected
    deltas   = report.get("risk_deltas", [])
    new      = report.get("new_risks", [])

    all_ids = (
        [d.get("risk_id") for d in deltas if d.get("delta_type") != "NO CHANGE"] +
        [r.get("risk_id") for r in new]
    )

    decisions = []
    for rid in all_ids:
        if rid in accepted:
            item = accepted[rid]
            decisions.append({
                "risk_id":       rid,
                "risk_title":    item.get("risk_title", ""),
                "delta_type":    item.get("delta_type", "NEW"),
                "decision":      "accepted",
                "reviewer_name": item.get("reviewer_name", "N/A"),
                "reviewer_role": item.get("reviewer_role", ""),
                "timestamp":     item.get("review_timestamp", str(date.today()))
            })
        elif rid in rejected:
            item = rejected[rid]
            decisions.append({
                "risk_id":       rid,
                "risk_title":    item.get("risk_title", ""),
                "delta_type":    item.get("delta_type", "NEW"),
                "decision":      "rejected",
                "reviewer_name": item.get("reviewer_name", "N/A"),
                "reviewer_role": item.get("reviewer_role", ""),
                "timestamp":     item.get("review_timestamp", str(date.today()))
            })
        else:
            decisions.append({
                "risk_id":   rid,
                "delta_type": "PENDING",
                "decision":  "pending",
                "timestamp": str(date.today())
            })

    return {
        "report_metadata":    report.get("report_metadata", {}),
        "overall_assessment": report.get("overall_assessment", {}),
        "delta_summary":      report.get("delta_summary", {}),
        "audit_trail": {
            "review_date":    str(date.today()),
            "total_reviewed": len(all_ids),
            "total_accepted": len(accepted),
            "total_rejected": len(rejected),
            "total_pending":  len(all_ids) - len(accepted) - len(rejected),
            "decisions":      decisions
        },
        "accepted_changes":   list(accepted.values()),
        "rejected_changes":   list(rejected.values()),
    }

# ── RUN BUTTON ────────────────────────────────────────────────
st.divider()
if st.button("🚀 Run Delta Analysis", type="primary", use_container_width=True):
    if not all([prev_rr_file, snapshot_file]):
        st.error("Please upload both required documents before running.")
    else:
        mrr_text = read_uploaded_file(mrr_file) if mrr_file else None
        msg = (
            "Comparing trial data against approved register and benchmarking "
            "against historical library... (45-90 seconds)"
            if mrr_text else
            "Comparing trial data against approved register... (30-60 seconds)"
        )
        with st.spinner(msg):
            prev_text     = read_uploaded_file(prev_rr_file)
            snapshot_text = read_uploaded_file(snapshot_file)
            report        = run_delta_analysis(prev_text, snapshot_text, mrr_text)
            st.session_state.report   = report
            st.session_state.accepted = {}
            st.session_state.rejected = {}
            st.session_state.run_history.append({
                "date":     str(date.today()),
                "study_id": report.get("report_metadata", {}).get("study_id", "N/A"),
                "drug":     report.get("report_metadata", {}).get("drug_name", "N/A"),
                "report":   report
            })
        st.success("✅ Delta analysis complete — review changes below.")
        st.divider()

# ── DISPLAY REPORT ────────────────────────────────────────────
if st.session_state.report:
    display_report(st.session_state.report)

    report          = st.session_state.report
    deltas          = report.get("risk_deltas", [])
    new             = report.get("new_risks", [])
    changed         = [d for d in deltas if d.get("delta_type") != "NO CHANGE"]
    total_to_review = len(changed) + len(new)
    total_reviewed  = len(st.session_state.accepted) + len(st.session_state.rejected)

    # ── EXPORT SECTION ────────────────────────────────────────
    st.divider()
    st.subheader("📤 Review Progress & Export")
    st.caption(
        "Export the final report for TMF filing and RBQM system update. "
        "Use the JSON file to import accepted changes directly into your "
        "risk register system. Use the PDF for TMF documentation."
    )

    progress = total_reviewed / total_to_review if total_to_review > 0 else 0
    st.progress(
        progress,
        text=f"{total_reviewed} of {total_to_review} changes reviewed — "
             f"{len(st.session_state.accepted)} accepted, "
             f"{len(st.session_state.rejected)} rejected"
    )

    if total_reviewed > 0:
        final_report = build_final_report(report)
        report_json  = json.dumps(final_report, indent=2)

        st.markdown("##### Download Options")
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="⬇️ Download JSON Report",
                data=report_json,
                file_name=f"delta_report_{date.today()}.json",
                mime="application/json",
                use_container_width=True,
                help="Import into your RBQM system or risk register to update accepted changes"
            )
            st.caption("📥 For RBQM system import and risk register update")
        with col2:
            pdf_bytes = generate_pdf(final_report)
            st.download_button(
                label="⬇️ Download PDF Report",
                data=pdf_bytes,
                file_name=f"delta_report_{date.today()}.pdf",
                mime="application/pdf",
                use_container_width=True,
                help="Formatted report for TMF filing and study team distribution"
            )
            st.caption("📁 For TMF filing and study team distribution")

        if total_to_review > total_reviewed:
            st.warning(
                f"⏳ {total_to_review - total_reviewed} changes still pending review. "
                "You can export now and continue reviewing, or complete all reviews first."
            )

# ── RUN HISTORY ───────────────────────────────────────────────
if st.session_state.run_history:
    st.divider()
    st.subheader(
        f"🕐 Run History ({len(st.session_state.run_history)} runs this session)"
    )
    for i, run in enumerate(reversed(st.session_state.run_history)):
        with st.expander(
            f"Run {len(st.session_state.run_history) - i} | "
            f"{run['drug']} | {run['study_id']} | {run['date']}"
        ):
            s = run["report"].get("delta_summary", {})
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Escalated",    s.get("escalated", 0))
            c2.metric("De-escalated", s.get("de_escalated", 0))
            c3.metric("New Risks",    s.get("new_risks", 0))
            c4.metric("Closed",       s.get("closed", 0))
            st.download_button(
                label="⬇️ Download Raw Report",
                data=json.dumps(run["report"], indent=2),
                file_name=f"delta_report_{run['study_id']}_{run['date']}.json",
                mime="application/json",
                key=f"history_{i}"
            )

# ── FOOTER ────────────────────────────────────────────────────
st.divider()
st.caption(
    "⚠️ This tool is for research and demonstration purposes. "
    "All outputs require qualified clinical review before use in "
    "regulated environments. Accepted changes should be validated "
    "by a qualified clinical risk manager before updating the risk register."
)