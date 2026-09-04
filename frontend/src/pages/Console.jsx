import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import AfterActionReport from "../components/AfterActionReport";
import ControlBar from "../components/ControlBar";
import GuidedDemo from "../components/GuidedDemo";
import IncidentDetail from "../components/IncidentDetail";
import IncidentList from "../components/IncidentList";
import MapView from "../components/MapView";
import ResourcePanel from "../components/ResourcePanel";
import ReplanComparison from "../components/ReplanComparison";
import SiteNav from "../components/SiteNav";
import StatsBar from "../components/StatsBar";
import { api, connectLive } from "../lib/api";

const empty = {
  status: { state: "idle" },
  incidents: [],
  resources: [],
  hospitals: [],
  predictions: [],
  stats: {},
  timeline: [],
  after_action_report: null,
};

const fallbackScenarios = [
  { id: "asu_game_night", label: "ASU game night" },
  { id: "monsoon_response", label: "Monsoon response" },
  { id: "weekday_commute", label: "Weekday commute" },
];

function replanKey(value) {
  const change = value?.changes?.[0];
  if (!change) return "";
  return [change.resource_id, change.from_incident, change.to_incident].join(":");
}

export default function Console() {
  const [state, setState] = useState(empty);
  const [selectedId, setSelectedId] = useState(null);
  const [detailsDismissed, setDetailsDismissed] = useState(false);
  const [alert, setAlert] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [scenarios, setScenarios] = useState(fallbackScenarios);
  const [scenarioId, setScenarioId] = useState("asu_game_night");
  const [guideActive, setGuideActive] = useState(false);
  const [guideStep, setGuideStep] = useState(0);
  const [replan, setReplan] = useState(null);
  const [report, setReport] = useState(null);
  const [resourceFocus, setResourceFocus] = useState(null);
  const dismissedReplanKey = useRef("");
  const resourceFocusTimer = useRef(null);

  const applySnapshot = useCallback((data) => {
    setState((prev) => ({ ...prev, ...data }));
  }, []);

  const refresh = useCallback(async () => {
    const data = await api.snapshot();
    applySnapshot(data);
    return data;
  }, [applySnapshot]);

  const showReplan = useCallback((value) => {
    if (!value?.changed || replanKey(value) === dismissedReplanKey.current) return;
    setReplan(value);
  }, []);

  const selectIncident = useCallback((id, options = {}) => {
    setDetailsDismissed(false);
    setSelectedId(id);

    window.clearTimeout(resourceFocusTimer.current);
    if (options.source === "resource") {
      const focus = {
        id,
        resourceId: options.resourceId,
        token: Date.now(),
        active: true,
      };
      setResourceFocus(focus);
      resourceFocusTimer.current = window.setTimeout(() => {
        setResourceFocus((current) => current?.token === focus.token
          ? { ...current, active: false }
          : current);
      }, 1600);
    } else {
      setResourceFocus(null);
    }
  }, []);

  const closeIncidentDetail = useCallback(() => {
    window.clearTimeout(resourceFocusTimer.current);
    setResourceFocus(null);
    setDetailsDismissed(true);
    setSelectedId(null);
  }, []);

  useEffect(() => () => window.clearTimeout(resourceFocusTimer.current), []);

  useEffect(() => {
    refresh().catch((err) => setError(err.message));
    api.scenarios().then(setScenarios).catch(() => {});
    const socket = connectLive((message) => {
      if (message.type === "snapshot") {
        applySnapshot(message.data);
      } else if (message.type === "status") {
        setState((prev) => ({ ...prev, status: message.data }));
      } else if (message.type === "stats") {
        setState((prev) => ({ ...prev, stats: message.data }));
      } else if (message.type === "resources") {
        setState((prev) => ({ ...prev, resources: message.data }));
      } else if (message.type === "timeline") {
        setState((prev) => ({ ...prev, timeline: message.data }));
      } else if (message.type === "incident") {
        setState((prev) => {
          const others = prev.incidents.filter((item) => item.id !== message.data.id);
          return { ...prev, incidents: [message.data, ...others] };
        });
      } else if (message.type === "reallocation") {
        showReplan(message.data);
        setAlert(message.data);
        window.setTimeout(() => setAlert(null), 8000);
      } else if (message.type === "alert") {
        setAlert(message.data);
        window.setTimeout(() => setAlert(null), 8000);
      }
    });
    return () => socket.close();
  }, [applySnapshot, refresh, showReplan]);

  useEffect(() => {
    if (state.status.scenario) setScenarioId(state.status.scenario);
  }, [state.status.scenario]);

  useEffect(() => {
    if (state.status.state !== "running") {
      return undefined;
    }
    const timer = window.setInterval(() => {
      refresh().catch(() => {});
    }, 1000);
    return () => window.clearInterval(timer);
  }, [refresh, state.status.state]);

  useEffect(() => {
    if (state.incidents.length === 0) {
      setSelectedId(null);
      setDetailsDismissed(false);
      return;
    }
    if (selectedId && !state.incidents.some((item) => item.id === selectedId)) {
      setSelectedId(null);
      return;
    }
    if (!selectedId && !detailsDismissed) {
      const next = state.incidents.find(
        (item) => !item.dispatcher_approved && item.status !== "Resolved"
      );
      setSelectedId((next || state.incidents[0]).id);
    }
  }, [detailsDismissed, selectedId, state.incidents]);

  async function run(action) {
    setBusy(true);
    setError("");
    try {
      const result = await action();
      if (result?.state) {
        setState((prev) => ({ ...prev, status: result }));
      }
      await refresh();
      return result;
    } catch (err) {
      setError(err.message || "Request failed");
    } finally {
      setBusy(false);
    }
  }

  const selected = useMemo(
    () => state.incidents.find((item) => item.id === selectedId) || null,
    [state.incidents, selectedId]
  );

  const selectedScenario = scenarios.find((item) => item.id === scenarioId) || scenarios[0];

  async function startScenario() {
    dismissedReplanKey.current = "";
    setReplan(null);
    return run(() => api.start({ scenario: scenarioId }));
  }

  async function resetScenario() {
    dismissedReplanKey.current = "";
    setReplan(null);
    setGuideStep(0);
    return run(api.reset);
  }

  async function injectIncident() {
    const result = await run(api.inject);
    showReplan(result?.reallocation);
    const injected = result?.incidents?.[0];
    if (injected) selectIncident(injected.id);
    return result;
  }

  function dismissReplan() {
    dismissedReplanKey.current = replanKey(replan);
    setReplan(null);
    setAlert(null);
  }

  async function approveIncident(id) {
    const result = await run(() => api.approve(id));
    if (!result?.dispatcher_approved) return result;

    closeIncidentDetail();
    if (replan?.changes?.[0]?.to_incident === id) dismissReplan();
    return result;
  }

  function chooseGuideIncident() {
    const candidates = state.incidents.filter(
      (item) =>
        !item.dispatcher_approved &&
        item.status !== "Resolved" &&
        item.context?.recommended_resource_id
    );
    const policeCandidate = candidates.find(
      (item) =>
        ["P3", "P4"].includes(item.severity) &&
        item.context.recommended_resource_id.startsWith("Police_")
    );
    const candidate = policeCandidate || candidates.find((item) => ["P3", "P4"].includes(item.severity)) || candidates[0];
    if (candidate) {
      selectIncident(candidate.id);
      setGuideStep(2);
    }
  }

  async function approveAndInject() {
    if (!selected) return;
    setBusy(true);
    setError("");
    try {
      await api.approve(selected.id);
      const result = await api.inject();
      showReplan(result?.reallocation);
      const injected = result?.incidents?.[0];
      if (injected) selectIncident(injected.id);
      await refresh();
      setGuideStep(3);
    } catch (err) {
      setError(err.message || "Guided demo action failed");
    } finally {
      setBusy(false);
    }
  }

  async function openReport() {
    try {
      const result = await api.report();
      setReport(result.data);
    } catch {
      setReport(state.after_action_report);
    }
  }

  async function runGuideAction() {
    if (guideStep === 0) {
      await startScenario();
      setGuideStep(1);
    } else if (guideStep === 1) {
      chooseGuideIncident();
    } else if (guideStep === 2) {
      await approveAndInject();
    } else {
      await openReport();
    }
  }

  const guideReady =
    guideStep === 0 ||
    guideStep === 3 ||
    (guideStep === 1 && state.incidents.some((item) => !item.dispatcher_approved)) ||
    (guideStep === 2 && selected && !selected.dispatcher_approved);

  return (
    <div className="app console">
      <SiteNav compact />
      <ControlBar
        status={state.status}
        busy={busy}
        scenarios={scenarios}
        scenarioId={scenarioId}
        onScenarioChange={setScenarioId}
        onStart={startScenario}
        onPause={() => run(api.pause)}
        onReset={resetScenario}
        onInject={injectIncident}
        onGuide={() => {
          setGuideActive(true);
          setGuideStep(0);
        }}
        onReport={openReport}
      />
      <StatsBar status={state.status} stats={state.stats} />
      {guideActive && (
        <GuidedDemo
          step={guideStep}
          ready={guideReady}
          busy={busy}
          scenarioLabel={selectedScenario?.label}
          onAction={runGuideAction}
          onBack={() => setGuideStep((value) => Math.max(0, value - 1))}
          onClose={() => setGuideActive(false)}
        />
      )}
      {error && <div className="alert-banner">{error}</div>}
      {alert && (
        <div className="alert-banner">
          <strong>{alert.title || "Reallocation"}</strong>
          <span>{alert.message}</span>
        </div>
      )}
      <main className="workspace">
        <IncidentList
          incidents={state.incidents}
          selectedId={selectedId}
          resourceFocus={resourceFocus}
          onSelect={selectIncident}
          onApprove={approveIncident}
          busy={busy}
        />
        <div className="map-wrap">
          <MapView
            incidents={state.incidents}
            resources={state.resources}
            hospitals={state.hospitals}
            predictions={state.predictions}
            selectedId={selectedId}
            resourceFocus={resourceFocus}
            onSelect={selectIncident}
          />
          <ReplanComparison replan={replan} onClose={dismissReplan} />
          <IncidentDetail
            key={`${selected?.id || "none"}-${resourceFocus?.token || 0}`}
            incident={selected}
            resourceFocus={resourceFocus}
            busy={busy}
            onClose={closeIncidentDetail}
            onApprove={approveIncident}
          />
        </div>
        <ResourcePanel
          resources={state.resources}
          incidents={state.incidents}
          hospitals={state.hospitals}
          predictions={state.predictions}
          timeline={state.timeline}
          focusedResourceId={resourceFocus?.active ? resourceFocus.resourceId : null}
          onSelectIncident={selectIncident}
        />
      </main>
      <AfterActionReport report={report} onClose={() => setReport(null)} />
    </div>
  );
}
