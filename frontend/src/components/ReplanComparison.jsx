import { X } from "./ui/icons";
import Button from "./ui/Button";

export default function ReplanComparison({ replan, onClose }) {
  if (!replan?.changed || !replan.changes?.length) return null;
  const change = replan.changes[0];
  return (
    <section className="replan-comparison" aria-live="polite">
      <div className="replan-heading">
        <div>
          <span className="section-kicker">Live re-plan</span>
          <strong>Higher-impact allocation found</strong>
        </div>
        <Button variant="ghost" size="icon-sm" onClick={onClose} aria-label="Close re-plan comparison"><X size={14} /></Button>
      </div>
      <div className="plan-flow">
        <div className="plan-state before">
          <span>Before</span>
          <strong>{change.resource_id?.replaceAll("_", " ")}</strong>
          <p>Responding to {change.from_incident || "existing incident"}</p>
        </div>
        <div className="replan-arrow">
          <span />
          <b>Re-route</b>
        </div>
        <div className="plan-state after">
          <span>Recommended now</span>
          <strong>{change.resource_id?.replaceAll("_", " ")}</strong>
          <p>{change.to_incident} · ETA {change.eta} min</p>
        </div>
      </div>
      <p className="replan-reason">{replan.message}</p>
    </section>
  );
}
