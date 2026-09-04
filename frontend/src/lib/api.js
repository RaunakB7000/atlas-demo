const API_URL = import.meta.env.VITE_API_URL || "";

function liveSocketUrl() {
  if (import.meta.env.VITE_WS_URL) {
    return `${import.meta.env.VITE_WS_URL}/ws/live`;
  }
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  return `${protocol}://${window.location.host}/ws/live`;
}

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  return response.json();
}

export const api = {
  snapshot: () => request("/api/snapshot"),
  scenarios: () => request("/api/simulation/scenarios"),
  report: () => request("/api/report"),
  start: (payload = {}) =>
    request("/api/simulation/start", { method: "POST", body: JSON.stringify(payload) }),
  pause: () => request("/api/simulation/pause", { method: "POST" }),
  reset: () => request("/api/simulation/reset", { method: "POST" }),
  inject: () => request("/api/simulation/inject", { method: "POST" }),
  approve: (incidentId) => request(`/api/incidents/${incidentId}/approve`, { method: "POST" }),
};

export function connectLive(onMessage) {
  let socket;
  let closed = false;
  let retries = 0;

  const open = () => {
    if (closed) {
      return;
    }
    socket = new WebSocket(liveSocketUrl());
    socket.onmessage = (event) => {
      try {
        onMessage(JSON.parse(event.data));
      } catch {
        /* ignore malformed frames */
      }
    };
    socket.onopen = () => {
      retries = 0;
    };
    socket.onclose = () => {
      if (closed) {
        return;
      }
      const delay = Math.min(4000, 400 * 2 ** retries);
      retries += 1;
      window.setTimeout(open, delay);
    };
  };

  open();
  return {
    close() {
      closed = true;
      if (socket) {
        socket.close();
      }
    },
  };
}
