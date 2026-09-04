import { Activity, AlertTriangle, Gauge, Layers3, Radio, Siren } from "./ui/icons";

const tiles = [
  ["incoming_reports", "Incoming reports", Radio],
  ["unique_incidents", "Unique incidents", Layers3],
  ["critical", "Critical", Siren],
  ["high_priority", "High priority", AlertTriangle],
  ["medium", "Medium", Activity],
];

export default function StatsBar({ status, stats }) {
  const values = {
    incoming_reports: status.incoming_reports ?? 0,
    unique_incidents: status.unique_incidents ?? 0,
    critical: status.critical ?? 0,
    high_priority: status.high_priority ?? 0,
    medium: status.medium ?? 0,
  };

  return (
    <section className="stats-bar">
      {tiles.map(([key, label, Icon]) => (
        <article key={key} className={`stat-tile ${key}`}>
          <span><Icon size={12} /> {label}</span>
          <strong>{values[key]}</strong>
        </article>
      ))}
      <article className="stat-tile">
        <span><Gauge size={12} /> Utilization</span>
        <strong>{Math.round((stats.utilization_rate || 0) * 100)}%</strong>
        <div className="stat-progress"><i style={{ width: `${Math.round((stats.utilization_rate || 0) * 100)}%` }} /></div>
      </article>
    </section>
  );
}
