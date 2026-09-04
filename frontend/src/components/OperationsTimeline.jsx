function formatTime(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    hour: "numeric",
    minute: "2-digit",
    second: "2-digit",
  }).format(new Date(value));
}

export default function OperationsTimeline({ events }) {
  const ordered = [...events].reverse();
  return (
    <div className="timeline-list">
      {ordered.length === 0 && (
        <div className="timeline-empty">
          <strong>No operational events yet</strong>
          <p>Start a scenario to build a timestamped decision log.</p>
        </div>
      )}
      {ordered.map((event) => (
        <article key={event.id} className={`timeline-event ${event.type}`}>
          <div className="timeline-marker" />
          <div>
            <div className="timeline-meta">
              <span>{event.type}</span>
              <time>{formatTime(event.timestamp)}</time>
            </div>
            <strong>{event.title}</strong>
            <p>{event.detail}</p>
          </div>
        </article>
      ))}
    </div>
  );
}
