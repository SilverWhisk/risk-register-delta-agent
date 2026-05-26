import anthropic
import json
import os
from datetime import date
from prompts import SYSTEM_PROMPT, build_user_prompt

client = anthropic.Anthropic()

def read_document(filepath):
    """Read a document from disk and return its text content."""
    with open(filepath, "r") as f:
        return f.read()

def run_delta_agent(previous_rr_path, snapshot_path, mrr_path=None):
    """
    Core agent function: compares trial data snapshot against
    approved risk register and generates a delta report.
    """
    print("\n📄 Reading documents...")
    previous_rr_text = read_document(previous_rr_path)
    snapshot_text    = read_document(snapshot_path)

    mrr_text = None
    if mrr_path and os.path.exists(mrr_path):
        mrr_text = read_document(mrr_path)
        print("✅ Documents loaded (including Master Risk Register).")
    else:
        print("✅ Documents loaded (no Master Risk Register provided).")

    print("\n🤖 Running delta analysis agent...")
    print("   (This may take 30-60 seconds)\n")

    raw_output = ""
    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=16000,
        system=SYSTEM_PROMPT,
        messages=[
            {
                "role": "user",
                "content": build_user_prompt(
                    previous_rr_text, snapshot_text, mrr_text
                )
            }
        ]
    ) as stream:
        for text in stream.text_stream:
            raw_output += text
            print(".", end="", flush=True)
    print("\n")

    try:
        return json.loads(raw_output)
    except json.JSONDecodeError:
        clean = raw_output.replace("```json", "").replace("```", "").strip()
        return json.loads(clean)

def display_results(report):
    """Print a human-readable summary of the delta report."""
    meta    = report.get("report_metadata", {})
    summary = report.get("delta_summary", {})
    deltas  = report.get("risk_deltas", [])
    new     = report.get("new_risks", [])
    overall = report.get("overall_assessment", {})

    print("=" * 60)
    print("       RISK REGISTER DELTA REPORT")
    print("=" * 60)
    print(f"\nStudy:           {meta.get('drug_name', 'N/A')}")
    print(f"Study ID:        {meta.get('study_id', 'N/A')}")
    print(f"Review Period:   {meta.get('review_period', 'N/A')}")
    print(f"Snapshot Date:   {meta.get('snapshot_date', 'N/A')}")
    print(f"Risks Reviewed:  {meta.get('total_risks_reviewed', 0)}")
    print(f"Historical Reg:  {'✅ Used' if meta.get('master_register_used') else '❌ Not provided'}")

    print(f"\n📊 DELTA SUMMARY")
    print("-" * 60)
    print(f"   🔴 Escalated:     {summary.get('escalated', 0)}")
    print(f"   🟢 De-escalated:  {summary.get('de_escalated', 0)}")
    print(f"   ✅ Closed:        {summary.get('closed', 0)}")
    print(f"   ⚪ No Change:     {summary.get('no_change', 0)}")
    print(f"   🆕 New Risks:     {summary.get('new_risks', 0)}")
    print(f"   Total Changes:   {summary.get('total_changes', 0)}")

    # Overall score
    print(f"\n🎯 OVERALL STUDY RISK SCORE")
    print("-" * 60)
    direction = overall.get("score_direction", "")
    arrow = {"INCREASED": "📈", "DECREASED": "📉", "STABLE": "➡️"}.get(direction, "")
    print(f"   Previous Score:  {overall.get('previous_study_risk_score', 'N/A')}/100")
    print(f"   Updated Score:   {overall.get('updated_study_risk_score', 'N/A')}/100  {arrow} {direction}")
    print(f"\n   {overall.get('narrative', '')}")

    # Risk deltas
    if deltas:
        print(f"\n📋 RISK CHANGES ({len(deltas)} risks reviewed)")
        print("-" * 60)
        for delta in deltas:
            icon = {
                "ESCALATED":    "🔴",
                "DE-ESCALATED": "🟢",
                "CLOSED":       "✅",
                "NO CHANGE":    "⚪"
            }.get(delta.get("delta_type"), "⚪")
            print(f"\n{icon} {delta.get('risk_id')} | {delta.get('risk_title')}")
            print(f"   {delta.get('previous_rating')} → {delta.get('recommended_rating')} | {delta.get('delta_type')}")
            print(f"   Why: {delta.get('reason')}")
            print(f"   Action: {delta.get('recommended_action')}")
            print(f"   Owner: {delta.get('owner')} | Urgency: {delta.get('urgency')}")

    # New risks
    if new:
        print(f"\n🆕 NEW RISKS ({len(new)} identified)")
        print("-" * 60)
        for risk in new:
            print(f"\n🆕 {risk.get('risk_id')} | {risk.get('risk_title')}")
            print(f"   Rating: {risk.get('recommended_rating')} | Domain: {risk.get('domain')}")
            print(f"   {risk.get('description')}")
            print(f"   Action: {risk.get('recommended_action')}")
            print(f"   Owner: {risk.get('owner')} | Urgency: {risk.get('urgency')}")

def human_review(report):
    """
    Human-in-the-loop checkpoint.
    Reviewer accepts or rejects each delta individually.
    """
    print("\n" + "=" * 60)
    print("           HUMAN REVIEW CHECKPOINT")
    print("=" * 60)
    print("\nReview each proposed change and accept or reject.")
    print("Only accepted changes will be included in the final report.\n")

    deltas   = report.get("risk_deltas", [])
    new      = report.get("new_risks", [])
    accepted = []
    rejected = []

    # Review existing risk changes
    for delta in deltas:
        if delta.get("delta_type") == "NO CHANGE":
            accepted.append({"type": "delta", "item": delta, "decision": "accepted"})
            continue

        icon = {
            "ESCALATED":    "🔴",
            "DE-ESCALATED": "🟢",
            "CLOSED":       "✅",
        }.get(delta.get("delta_type"), "⚪")

        print(f"{icon} {delta.get('risk_id')} | {delta.get('risk_title')}")
        print(f"   Proposed: {delta.get('previous_rating')} → {delta.get('recommended_rating')} ({delta.get('delta_type')})")
        print(f"   Reason: {delta.get('reason')}")
        decision = input("   Accept this change? (yes/no): ").strip().lower()

        if decision in ["yes", "y"]:
            accepted.append({"type": "delta", "item": delta, "decision": "accepted"})
            print("   ✅ Accepted\n")
        else:
            rejected.append({"type": "delta", "item": delta, "decision": "rejected"})
            print("   ❌ Rejected\n")

    # Review new risks
    for risk in new:
        print(f"🆕 NEW: {risk.get('risk_id')} | {risk.get('risk_title')}")
        print(f"   Rating: {risk.get('recommended_rating')} | {risk.get('description')}")
        decision = input("   Accept this new risk? (yes/no): ").strip().lower()

        if decision in ["yes", "y"]:
            accepted.append({"type": "new", "item": risk, "decision": "accepted"})
            print("   ✅ Accepted\n")
        else:
            rejected.append({"type": "new", "item": risk, "decision": "rejected"})
            print("   ❌ Rejected\n")

    return accepted, rejected

def build_audit_trail(accepted, rejected, report):
    """Build a full audit trail of all review decisions."""
    return {
        "audit_trail": {
            "review_date": str(date.today()),
            "study_id": report.get("report_metadata", {}).get("study_id", "N/A"),
            "total_reviewed": len(accepted) + len(rejected),
            "total_accepted": len(accepted),
            "total_rejected": len(rejected),
            "decisions": [
                {
                    "risk_id": d["item"].get("risk_id"),
                    "risk_title": d["item"].get("risk_title"),
                    "delta_type": d["item"].get("delta_type", "NEW"),
                    "decision": d["decision"],
                    "timestamp": str(date.today())
                }
                for d in accepted + rejected
            ]
        },
        "accepted_changes": [d["item"] for d in accepted],
        "rejected_changes": [d["item"] for d in rejected],
        "report_metadata": report.get("report_metadata", {}),
        "overall_assessment": report.get("overall_assessment", {})
    }

def save_report(final_report, output_path):
    """Save the final approved delta report with audit trail."""
    with open(output_path, "w") as f:
        json.dump(final_report, f, indent=2)
    print(f"\n✅ Delta report with audit trail saved to: {output_path}")

def main():
    previous_rr_path = "documents/mock_previous_risk_register.md"
    snapshot_path    = "documents/mock_trial_data_snapshot.md"
    mrr_path         = "documents/mock_master_risk_register.md"  # set to None to skip

    output_path = f"outputs/delta_report_{date.today()}.json"

    report = run_delta_agent(previous_rr_path, snapshot_path, mrr_path)
    display_results(report)

    accepted, rejected = human_review(report)
    final_report = build_audit_trail(accepted, rejected, report)
    save_report(final_report, output_path)

if __name__ == "__main__":
    main()