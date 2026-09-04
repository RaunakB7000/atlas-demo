import { useEffect, useMemo, useRef, useState } from "react";
import { Check, Search, X } from "./ui/icons";
import Button from "./ui/Button";

const severityRank = { P1: 0, P2: 1, P3: 2, P4: 3 };

function displayId(value) {
  return value?.replaceAll("_", " ") || "Calculating";
}

export default function IncidentList({ incidents, selectedId, resourceFocus, onSelect, onApprove, busy }) {
  const [searchOpen, setSearchOpen] = useState(false);
  const [query, setQuery] = useState("");
  const cardRefs = useRef(new Map());
  const sorted = useMemo(() => {
    const search = query.trim().toLowerCase();
    return [...incidents]
      .filter((incident) => {
        if (!search) return true;
        return [
          incident.id,
          incident.incident_type,
          incident.severity,
          incident.status,
          incident.transcript,
          incident.assigned_resource,
          incident.context?.recommended_resource_id,
        ]
          .filter(Boolean)
          .some((value) => String(value).replaceAll("_", " ").toLowerCase().includes(search));
      })
      .sort((a, b) => {
        const severity = (severityRank[a.severity] ?? 9) - (severityRank[b.severity] ?? 9);
        return severity || b.call_count - a.call_count;
      });
  }, [incidents, query]);

  function toggleSearch() {
    setSearchOpen((open) => {
      if (open) setQuery("");
      return !open;
    });
  }

  useEffect(() => {
    cardRefs.current.get(selectedId)?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [resourceFocus?.token, selectedId]);

  return (
    <aside className="panel">
      <div className="panel-header">
        <h2>Incidents</h2>
        <div className="panel-header-actions">
          <span>{query ? `${sorted.length}/${incidents.length}` : incidents.length}</span>
          <Button
            variant="ghost"
            size="icon-sm"
            className={`incident-search-toggle ${searchOpen ? "active" : ""}`}
            onClick={toggleSearch}
            aria-label={searchOpen ? "Close incident search" : "Search incidents"}
            title={searchOpen ? "Close search" : "Search incidents"}
          >
            <Search size={14} />
          </Button>
        </div>
      </div>
      {searchOpen && (
        <div className="incident-search">
          <Search size={14} aria-hidden="true" />
          <input
            autoFocus
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="ID, type, priority, status…"
            aria-label="Search incidents"
          />
          {query && (
            <Button variant="ghost" size="icon-xs" onClick={() => setQuery("")} aria-label="Clear incident search"><X size={12} /></Button>
          )}
        </div>
      )}
      <div className="list">
        {sorted.length === 0 && (
          <p className="empty">
            {query ? `No incidents match “${query}”.` : "Waiting for incoming 911 reports."}
          </p>
        )}
        {sorted.map((incident) => {
          const resolved = incident.status === "Resolved";
          const canApprove = !incident.dispatcher_approved && !resolved;
          return (
            <article
              key={`${incident.id}-${resourceFocus?.id === incident.id ? resourceFocus.token : "base"}`}
              ref={(element) => {
                if (element) cardRefs.current.set(incident.id, element);
                else cardRefs.current.delete(incident.id);
              }}
              className={`incident-card ${selectedId === incident.id ? "active" : ""} ${resourceFocus?.active && resourceFocus.id === incident.id ? "resource-focus-pulse" : ""}`}
              onClick={() => onSelect(incident.id)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  onSelect(incident.id);
                }
              }}
              role="button"
              tabIndex={0}
            >
              <div className="card-top">
                <span className={`badge ${incident.severity}`}>{incident.severity}</span>
                <span className="muted">{incident.incident_type}</span>
              </div>
              <p>{incident.transcript}</p>
              <div className="card-meta">
                <span>{incident.call_count} call{incident.call_count === 1 ? "" : "s"}</span>
                <span>{Math.round(incident.confidence * 100)}% conf.</span>
              </div>
              <div className="incident-workflow">
                <span className={`workflow-state ${incident.status.toLowerCase().replaceAll(" ", "-")}`}>
                  {incident.status}
                </span>
                {canApprove ? (
                  <Button
                    variant="secondary"
                    size="xs"
                    className="quick-approve"
                    disabled={busy}
                    onClick={(event) => {
                      event.stopPropagation();
                      onSelect(incident.id);
                      onApprove(incident.id);
                    }}
                  >
                    <Check size={11} /> Approve &amp; dispatch
                  </Button>
                ) : (
                  <span className="assigned-unit">
                    {resolved ? "Complete" : displayId(incident.assigned_resource)}
                  </span>
                )}
              </div>
              {canApprove && (
                <p className="recommendation-line">
                  Recommended: {displayId(incident.context?.recommended_resource_id)}
                </p>
              )}
            </article>
          );
        })}
      </div>
    </aside>
  );
}
