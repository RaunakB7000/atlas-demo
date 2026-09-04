import { useEffect } from "react";
import { Circle, CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";

const severityColor = {
  P1: "#ef4444",
  P2: "#f97316",
  P3: "#eab308",
  P4: "#22c55e",
};

const resourceColor = {
  Ambulance: "#38bdf8",
  "Fire Truck": "#fb7185",
  Police: "#a78bfa",
  "Air Ambulance": "#2dd4bf",
};

const maptilerKey = import.meta.env.VITE_MAPTILER_KEY;

function SelectionController({ incident }) {
  const map = useMap();

  useEffect(() => {
    if (!incident?.location) return;
    map.flyTo(
      [incident.location.lat, incident.location.lng],
      Math.max(map.getZoom(), 14),
      { duration: 0.55 }
    );
  }, [incident?.id, incident?.location?.lat, incident?.location?.lng, map]);

  return null;
}

export default function MapView({ incidents, resources, hospitals, predictions, selectedId, resourceFocus, onSelect }) {
  const selectedIncident = incidents.find((incident) => incident.id === selectedId);
  const recommendedResourceIds = new Set(
    incidents
      .filter((incident) => !incident.dispatcher_approved && incident.status !== "Resolved")
      .map((incident) => incident.context?.recommended_resource_id)
      .filter(Boolean)
  );
  const tiles = maptilerKey
    ? {
        url: `https://api.maptiler.com/maps/dataviz-dark/{z}/{x}/{y}.png?key=${maptilerKey}`,
        attribution: "&copy; MapTiler &copy; OpenStreetMap contributors",
      }
    : {
        url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attribution: "&copy; OpenStreetMap",
      };

  return (
    <MapContainer center={[33.415, -111.935]} zoom={13} className="map" scrollWheelZoom>
      <TileLayer attribution={tiles.attribution} url={tiles.url} />
      <SelectionController incident={selectedIncident} />
      {predictions.map((item) => (
        <Circle
          key={`pred-${item.id}`}
          center={[item.lat, item.lng]}
          radius={500 + item.probability * 700}
          pathOptions={{ color: "#38bdf8", fillOpacity: 0.08, weight: 1 }}
        >
          <Popup>
            <strong>{item.label}</strong>
            <br />
            Elevated probability {Math.round(item.probability * 100)}%
          </Popup>
        </Circle>
      ))}
      {incidents.map((incident) => {
        const focusedFromResource = resourceFocus?.active && resourceFocus.id === incident.id;
        const resourceFocusKey = resourceFocus?.id === incident.id ? resourceFocus.token : "base";
        return (
        <CircleMarker
          key={`${incident.id}-${resourceFocusKey}`}
          center={[incident.location.lat, incident.location.lng]}
          radius={selectedId === incident.id ? 12 : 8}
          pathOptions={{
            color: severityColor[incident.severity] || "#94a3b8",
            fillColor: severityColor[incident.severity] || "#94a3b8",
            fillOpacity: 0.9,
            weight: selectedId === incident.id ? 3 : 1,
            className: focusedFromResource ? "resource-focus-marker" : "",
          }}
          eventHandlers={{ click: () => onSelect(incident.id) }}
        >
          <Popup>
            <strong>
              {incident.severity} {incident.incident_type}
            </strong>
            <br />
            {incident.transcript}
          </Popup>
        </CircleMarker>
        );
      })}
      {resources.map((resource) => (
        <CircleMarker
          key={resource.id}
          center={[resource.location.lat, resource.location.lng]}
          radius={recommendedResourceIds.has(resource.id) || resource.status !== "Available" ? 7 : 5}
          pathOptions={{
            color: recommendedResourceIds.has(resource.id)
              ? "#3ee0c6"
              : resourceColor[resource.type] || "#fff",
            fillColor: resourceColor[resource.type] || "#fff",
            fillOpacity: resource.status === "Available" ? 0.45 : 1,
            weight: recommendedResourceIds.has(resource.id) || resource.status !== "Available" ? 3 : 1,
          }}
        >
          <Popup>
            {resource.id.replaceAll("_", " ")}
            <br />
            {resource.status}
            {recommendedResourceIds.has(resource.id) ? " · Recommended" : ""}
            {resource.eta ? ` · ${resource.eta} min` : ""}
          </Popup>
        </CircleMarker>
      ))}
      {hospitals.map((hospital) => (
        <CircleMarker
          key={hospital.id}
          center={[hospital.location.lat, hospital.location.lng]}
          radius={7}
          pathOptions={{ color: "#f8fafc", fillColor: "#64748b", fillOpacity: 0.9 }}
        >
          <Popup>
            {hospital.name}
            <br />
            {hospital.available_beds} open beds
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
