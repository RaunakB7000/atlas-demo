import { FileChartColumn, Pause, Play, RefreshCcw, Route, ShieldAlert } from "./ui/icons";
import Button from "./ui/Button";

export default function ControlBar({
  status,
  busy,
  scenarios,
  scenarioId,
  onScenarioChange,
  onStart,
  onPause,
  onReset,
  onInject,
  onGuide,
  onReport,
}) {
  const running = status.state === "running";
  const paused = status.state === "paused";
  return (
    <header className="topbar">
      <div className="operations-title">
        <p className="eyebrow">Phoenix–Tempe unified operations</p>
        <h1>Operations</h1>
      </div>
      <label className="scenario-control">
        <span>Scenario</span>
        <select value={scenarioId} onChange={(event) => onScenarioChange(event.target.value)} disabled={running || busy}>
          {scenarios.map((scenario) => (
            <option key={scenario.id} value={scenario.id}>{scenario.label}</option>
          ))}
        </select>
      </label>
      <div className="status-block">
        <span className={`status-dot ${status.state}`} />
        <div>
          <span>System status</span>
          <strong>{status.state || "idle"}</strong>
        </div>
      </div>
      <div className="controls">
        <Button variant="ghost" size="sm" onClick={onGuide} disabled={busy}><Route size={14} /> Guided demo</Button>
        <Button variant="ghost" size="sm" onClick={onReport}><FileChartColumn size={14} /> Report</Button>
        <Button variant="primary" size="sm" onClick={onStart} disabled={running || busy}>
          <Play size={14} fill="currentColor" /> {running ? "Scenario running" : paused ? "Resume" : "Start scenario"}
        </Button>
        <Button variant="outline" size="icon-sm" onClick={onPause} disabled={!running} title="Pause scenario" aria-label="Pause scenario">
          <Pause size={14} fill="currentColor" />
        </Button>
        <Button variant="destructive" size="sm" onClick={onInject} disabled={busy}>
          <ShieldAlert size={14} /> Inject P1
        </Button>
        <Button variant="outline" size="icon-sm" onClick={onReset} disabled={busy} title="Reset scenario" aria-label="Reset scenario">
          <RefreshCcw size={14} />
        </Button>
      </div>
    </header>
  );
}
