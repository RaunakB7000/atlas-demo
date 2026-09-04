import { useState } from "react";
import { Activity, ChevronDown, ExternalLink, ListFilter } from "./ui/icons";
import OperationsTimeline from "./OperationsTimeline";
import Button from "./ui/Button";

const severityRank = { P1: 0, P2: 1, P3: 2, P4: 3 };

export default function ResourcePanel({
  resources,
  incidents,
  hospitals,
  predictions,
  timeline = [],
  focusedResourceId,
  onSelectIncident,
}) {
  const [activeTab, setActiveTab] = useState("resources");
  const [expandedResource, setExpandedResource] = useState(null);
  const [resourceFilter, setResourceFilter] = useState("all");
  const available = resources.filter((item) => item.status === "Available").length;
  const recommendations = new Map();

  [...incidents]
    .filter((incident) => !incident.dispatcher_approved && incident.status !== "Resolved")
    .sort((a, b) => (severityRank[a.severity] ?? 9) - (severityRank[b.severity] ?? 9))
    .forEach((incident) => {
      const resourceId = incident.context?.recommended_resource_id;
      if (!resourceId) return;
      const existing = recommendations.get(resourceId) || [];
      recommendations.set(resourceId, [...existing, incident]);
    });

  const orderedResources = [...resources].sort((a, b) => {
    const aActive = a.status === "Available" ? 1 : 0;
    const bActive = b.status === "Available" ? 1 : 0;
    if (aActive !== bActive) return aActive - bActive;
    const aRecommended = recommendations.has(a.id) ? 0 : 1;
    const bRecommended = recommendations.has(b.id) ? 0 : 1;
    return aRecommended - bRecommended || a.id.localeCompare(b.id);
  });

  const activeCount = resources.length - available;
  const visibleResources = orderedResources.filter((resource) => {
    if (resourceFilter === "recommended") return recommendations.has(resource.id);
    if (resourceFilter === "active") return resource.status !== "Available";
    return true;
  });

  function openIncident(incidentId, resourceId) {
    onSelectIncident(incidentId, { source: "resource", resourceId });
  }

  function incidentLabel(incident) {
    return `${incident.severity} · ${incident.id} · ${incident.incident_type}`;
  }

  return (
    <aside className="panel resource-panel">
      <div className="rail-tabs">
        <Button variant="ghost" size="sm" className={activeTab === "resources" ? "active" : ""} onClick={() => setActiveTab("resources")}><ListFilter size={13} /> Resources</Button>
        <Button variant="ghost" size="sm" className={activeTab === "timeline" ? "active" : ""} onClick={() => setActiveTab("timeline")}><Activity size={13} /> Timeline <span>{timeline.length}</span></Button>
      </div>
      {activeTab === "timeline" ? (
        <OperationsTimeline events={timeline} />
      ) : (
        <>
        <div className="panel-header resource-summary">
          <strong>{available}/{resources.length} available</strong>
          <span>{recommendations.size} units recommended</span>
        </div>
        <div className="resource-filters" aria-label="Filter resources">
          {[
            ["all", "All", resources.length],
            ["recommended", "Suggested", recommendations.size],
            ["active", "Active", activeCount],
          ].map(([value, label, count]) => (
            <Button
              key={value}
              variant="ghost"
              size="xs"
              className={resourceFilter === value ? "active" : ""}
              onClick={() => {
                setResourceFilter(value);
                setExpandedResource(null);
              }}
            >
              {label}<span>{count}</span>
            </Button>
          ))}
        </div>
        <div className="resource-panel-scroll">
        <div className="resource-list">
        {visibleResources.length === 0 && (
          <div className="resource-empty">
            <strong>No resources here</strong>
            <p>Try another filter to see the full fleet.</p>
          </div>
        )}
        {visibleResources.map((resource) => {
          const recommendedFor = recommendations.get(resource.id) || [];
          const leadRecommendation = recommendedFor[0];
          const active = resource.status !== "Available";
          return (
          <div
            key={resource.id}
            className={`resource-row ${active ? "resource-active" : ""} ${recommendedFor.length ? "resource-recommended" : ""} ${focusedResourceId === resource.id ? "resource-focused" : ""}`}
          >
            <div>
              <div className="resource-name-row">
                <span className={`resource-type-dot ${resource.type.toLowerCase().replaceAll(" ", "-")}`} />
                <strong>{resource.id.replaceAll("_", " ")}</strong>
              </div>
              <p className="resource-status-line">
                <span className={`availability-dot ${resource.status.replaceAll(" ", "-").toLowerCase()}`} />
                <span>{resource.status}</span>
                {resource.eta ? ` · ETA ${resource.eta} min` : ""}
              </p>
              {active && resource.current_incident_id && (
                <div className="resource-recommendation-card active-assignment">
                  <div className="assignment-copy">
                    <span>Assigned to</span>
                    <strong>{resource.current_incident_id}</strong>
                  </div>
                  <Button
                    variant="outline"
                    size="xs"
                    className="resource-view-button"
                    onClick={() => openIncident(resource.current_incident_id, resource.id)}
                    aria-label={`View assigned incident ${resource.current_incident_id}`}
                  >
                    View <ExternalLink size={11} aria-hidden="true" />
                  </Button>
                </div>
              )}
              {!active && leadRecommendation && (
                <div className="resource-recommendations">
                  <div className="resource-recommendation-card recommended-assignment">
                    <div className="assignment-copy">
                      <span>Recommended for</span>
                      <strong>{incidentLabel(leadRecommendation)}</strong>
                    </div>
                    <Button
                      variant="outline"
                      size="xs"
                      className="resource-view-button"
                      onClick={() => openIncident(leadRecommendation.id, resource.id)}
                      aria-label={`View ${incidentLabel(leadRecommendation)}`}
                    >
                      View <ExternalLink size={11} aria-hidden="true" />
                    </Button>
                  </div>
                  {recommendedFor.length > 1 && (
                    <Button
                      variant="ghost"
                      size="xs"
                      className="more-recommendations"
                      onClick={() => setExpandedResource(
                        expandedResource === resource.id ? null : resource.id
                      )}
                      aria-expanded={expandedResource === resource.id}
                    >
                      <span>+{recommendedFor.length - 1} more</span>
                      <ChevronDown className="menu-chevron" size={13} aria-hidden="true" />
                    </Button>
                  )}
                  {expandedResource === resource.id && (
                    <div className="recommendation-menu" aria-label={`Other recommendations for ${resource.id.replaceAll("_", " ")}`}>
                      {recommendedFor.slice(1).map((incident) => (
                        <div className="recommendation-menu-item" key={incident.id}>
                          <div>
                            <span className={`badge ${incident.severity}`}>{incident.severity}</span>
                            <span className="menu-incident-copy">
                              <strong>{incident.id}</strong>
                              <small>{incident.incident_type}</small>
                            </span>
                          </div>
                          <Button
                            variant="ghost"
                            size="xs"
                            onClick={() => openIncident(incident.id, resource.id)}
                            aria-label={`View ${incidentLabel(incident)}`}
                          >
                            View <ExternalLink size={11} aria-hidden="true" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
            <span className={`status-chip ${resource.status.replace(" ", "-").toLowerCase()}`}>
              {resource.type}
            </span>
          </div>
          );
        })}
        </div>
        <div className="panel-header subsection-header">
          <h2>Hospitals</h2>
        </div>
        {hospitals.map((hospital) => (
          <div key={hospital.id} className="resource-row">
            <div>
              <strong>{hospital.name}</strong>
              <p>
                {hospital.available_beds} open / {hospital.capacity} beds
              </p>
            </div>
          </div>
        ))}
        <div className="panel-header subsection-header">
          <h2>Predicted demand</h2>
        </div>
        {predictions.map((item) => (
          <div key={item.id} className="resource-row">
            <div>
              <strong>{item.label}</strong>
              <p>{item.recommendation}</p>
            </div>
            <span className="status-chip">{Math.round(item.probability * 100)}%</span>
          </div>
        ))}
        </div>
        </>
      )}
    </aside>
  );
}
