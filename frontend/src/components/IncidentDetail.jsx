import { Check, Send, X } from "./ui/icons";
import Button from "./ui/Button";

export default function IncidentDetail({ incident, resourceFocus, onApprove, onClose, busy }) {
  if (!incident) {
    return (
      <div className="map-tip">Select an incident to review the recommended response.</div>
    );
  }

  const signals = incident.context?.signals || [];
  const resolved = incident.status === "Resolved";
  const recommendedUnit = incident.context?.recommended_resource_id?.replaceAll("_", " ");
  const explanation = incident.context?.recommendation_explanation;
  const alternatives = incident.context?.recommendation_alternatives || [];
  const actionLabel = resolved
    ? "Incident resolved"
    : incident.dispatcher_approved
      ? "Dispatcher approved"
      : "Approve & dispatch";

  return (
    <section className={`detail selected-detail ${resourceFocus?.active && resourceFocus.id === incident.id ? "resource-focus-detail" : ""}`}>
      <div className="detail-heading">
        <div className="detail-heading-copy">
          <div className="detail-title-row">
            <span className={`badge ${incident.severity}`}>{incident.severity}</span>
            <span className={`workflow-state ${incident.status.toLowerCase().replaceAll(" ", "-")}`}>
              {incident.status}
            </span>
            {resourceFocus?.active && resourceFocus.id === incident.id && (
              <span className="resource-origin-label">Opened from resources</span>
            )}
          </div>
          <h3>
            {incident.id} · {incident.incident_type}
          </h3>
        </div>
        <Button variant="ghost" size="icon-sm" className="close-detail" onClick={onClose} aria-label="Close incident details"><X size={15} /></Button>
      </div>
      <p className="detail-transcript" title={incident.transcript}>{incident.transcript}</p>
      <dl>
        <div>
          <dt>Clustered calls</dt>
          <dd>{incident.call_count}</dd>
        </div>
        <div>
          <dt>Confidence</dt>
          <dd>{Math.round(incident.confidence * 100)}%</dd>
        </div>
        <div>
          <dt>Recommended response</dt>
          <dd>{recommendedUnit || incident.recommended_response || "Calculating"}</dd>
        </div>
        <div>
          <dt>Status</dt>
          <dd>{incident.status}</dd>
        </div>
      </dl>
      {(signals.length > 0 || incident.context?.severity_rationale) && (
        <div className="detail-insights">
          {signals.length > 0 && <p className="signals">Signals: {signals.join(", ")}</p>}
          {incident.context?.severity_rationale && (
            <p className="rationale">{incident.context.severity_rationale}</p>
          )}
        </div>
      )}
      {explanation && (
        <details className="explanation-panel">
          <summary>
            <span>
              <strong>Why this recommendation</strong>
              <small>{Math.round((explanation.confidence || 0) * 100)}% decision confidence</small>
            </span>
            <span className="disclosure">Details</span>
          </summary>
          <p className="explanation-summary">{explanation.summary}</p>
          <div className="factor-grid">
            {explanation.factors?.map((factor) => (
              <article key={factor.label}>
                <div>
                  <span>{factor.label}</span>
                  <strong>{factor.value}</strong>
                </div>
                <div className="score-track" aria-label={`${factor.score} out of 100`}>
                  <span style={{ width: `${factor.score}%` }} />
                </div>
                <p>{factor.detail}</p>
              </article>
            ))}
          </div>
          {alternatives.length > 0 && (
            <div className="alternatives-row">
              <span>Alternatives considered</span>
              {alternatives.map((item) => (
                <strong key={item.resource_id}>
                  {item.resource_id.replaceAll("_", " ")} · {item.eta} min
                </strong>
              ))}
            </div>
          )}
          <p className="policy-note">Policy: {explanation.policy}</p>
        </details>
      )}
      <div className="detail-actions">
        <p>
          {incident.dispatcher_approved
            ? `Assigned unit: ${incident.assigned_resource?.replaceAll("_", " ") || recommendedUnit || "Pending"}`
            : "Atlas recommends. You approve before any unit is dispatched."}
        </p>
        <Button
          variant="primary"
          size="sm"
          disabled={busy || incident.dispatcher_approved || resolved}
          onClick={() => onApprove(incident.id)}
        >
          {incident.dispatcher_approved || resolved ? <Check size={14} /> : <Send size={14} />}{actionLabel}
        </Button>
      </div>
    </section>
  );
}
