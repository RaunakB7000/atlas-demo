import { Download, X } from "./ui/icons";
import Button from "./ui/Button";

const metricLabels = {
  incoming_reports: "Reports analyzed",
  unique_incidents: "Unique incidents",
  duplicates_consolidated: "Duplicates consolidated",
  noise_reduction_percent: "Noise reduction",
  critical_incidents: "Critical incidents",
  dispatcher_approvals: "Approved dispatches",
  resolved_incidents: "Resolved incidents",
  peak_utilization_percent: "Peak utilization",
};

function metricValue(key, value) {
  return key.endsWith("percent") ? `${value}%` : value;
}

export default function AfterActionReport({ report, onClose }) {
  if (!report) return null;

  function downloadReport() {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `atlas-${report.scenario?.id || "scenario"}-report.json`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="modal-backdrop" role="presentation" onMouseDown={onClose}>
      <section className="report-modal" role="dialog" aria-modal="true" aria-labelledby="report-title" onMouseDown={(event) => event.stopPropagation()}>
        <header className="report-header">
          <div>
            <span className="section-kicker">After-action report</span>
            <h2 id="report-title">{report.scenario?.label || "Operational scenario"}</h2>
            <p>{report.scenario?.description}</p>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close report"><X size={16} /></Button>
        </header>
        <div className="report-metrics">
          {Object.entries(report.metrics || {})
            .filter(([key]) => metricLabels[key])
            .map(([key, value]) => (
              <article key={key}>
                <span>{metricLabels[key]}</span>
                <strong>{metricValue(key, value)}</strong>
              </article>
            ))}
        </div>
        <div className="report-columns">
          <div>
            <h3>Operational highlights</h3>
            <ul>{report.highlights?.map((item) => <li key={item}>{item}</li>)}</ul>
          </div>
          <div>
            <h3>Recommended follow-up</h3>
            <ul>{report.recommendations?.map((item) => <li key={item}>{item}</li>)}</ul>
          </div>
        </div>
        <footer className="report-footer">
          <span>Generated from the current synthetic decision log.</span>
          <Button variant="primary" onClick={downloadReport}><Download size={15} /> Download report</Button>
        </footer>
      </section>
    </div>
  );
}
