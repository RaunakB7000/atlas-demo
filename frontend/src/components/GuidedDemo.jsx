import { ArrowLeft, ArrowRight, X } from "./ui/icons";
import Button from "./ui/Button";

const steps = [
  {
    eyebrow: "Step 1 of 4 · Establish the picture",
    title: "Start a deterministic incident surge",
    body: "Atlas will replay the selected scenario with the same reports, locations, and recommendations every time.",
    action: "Start guided scenario",
  },
  {
    eyebrow: "Step 2 of 4 · Human review",
    title: "Inspect a lower-priority recommendation",
    body: "Open a recommendation and review the unit, ETA, capability match, and alternatives before approving it.",
    action: "Review recommendation",
  },
  {
    eyebrow: "Step 3 of 4 · Stress the plan",
    title: "Approve, then introduce a P1 incident",
    body: "The approved unit starts moving. A new critical collision then forces Atlas to compare the current plan with a better one.",
    action: "Approve and inject P1",
  },
  {
    eyebrow: "Step 4 of 4 · Review the outcome",
    title: "The operational plan has been recalculated",
    body: "Review the before/after decision, timeline, and after-action metrics prepared for the debrief.",
    action: "Open after-action report",
  },
];

export default function GuidedDemo({
  step,
  ready,
  onAction,
  onBack,
  onClose,
  busy,
  scenarioLabel,
}) {
  const current = steps[Math.min(step, steps.length - 1)];
  return (
    <section className="guided-bar" aria-label="Guided demo">
      <div className="guide-progress" aria-hidden="true">
        {steps.map((_, index) => (
          <span key={index} className={index <= step ? "complete" : ""} />
        ))}
      </div>
      <div className="guide-copy">
        <p>{current.eyebrow}</p>
        <strong>{current.title}</strong>
        <span>{current.body}</span>
      </div>
      <div className="guide-context">
        <span>Scenario</span>
        <strong>{scenarioLabel}</strong>
      </div>
      <div className="guide-actions">
        {step > 0 && <Button variant="outline" size="sm" onClick={onBack}><ArrowLeft size={13} /> Back</Button>}
        <Button variant="primary" size="sm" onClick={onAction} disabled={busy || !ready}>
          {busy ? "Working…" : current.action} {!busy && <ArrowRight size={13} />}
        </Button>
        <Button variant="ghost" size="icon-sm" onClick={onClose} aria-label="Exit guided demo"><X size={14} /></Button>
      </div>
    </section>
  );
}
