import { Link } from "react-router-dom";
import { Activity, ArrowRight, GitMerge, Play, Radar, RefreshCw, Route, ShieldCheck, Sparkles } from "../components/ui/icons";
import SiteFooter from "../components/SiteFooter";
import SiteNav from "../components/SiteNav";
import { buttonClass } from "../components/ui/Button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/Card";

const capabilities = [
  {
    num: "01",
    icon: Activity,
    title: "Concurrent call processing",
    body: "AIR workers read hundreds of 911 transcripts at once and extract type, severity, address, injuries, hazards, and people count.",
  },
  {
    num: "02",
    icon: GitMerge,
    title: "Duplicate detection",
    body: "500 callers can be describing 127 events. Atlas clusters by geography, time, and AIR embeddings.",
  },
  {
    num: "03",
    icon: ShieldCheck,
    title: "Severity as advice",
    body: "P1 through P4 recommendations. A human dispatcher still approves. No autonomous life-or-death dispatch.",
  },
  {
    num: "04",
    icon: Route,
    title: "Resource allocation",
    body: "Ambulances, engines, police, hospital beds, and travel time scored together — not one call at a time.",
  },
  {
    num: "05",
    icon: RefreshCw,
    title: "Continuous re-planning",
    body: "A new cardiac arrest or a closed highway forces Atlas to recompute. Observe, analyze, plan, recommend, repeat.",
  },
  {
    num: "06",
    icon: Radar,
    title: "Demand prediction",
    body: "Friday 11pm on Mill Ave. Atlas forecasts where the next hour of calls is likely — and where to stage units now.",
  },
];

const flow = [
  { k: "Start", v: "Synthetic 911 traffic streams across Tempe and Phoenix." },
  { k: "Cluster", v: "Incoming reports collapse into unique incidents on the map." },
  { k: "Recommend", v: "Each incident gets a unit, an ETA, and a hospital if needed." },
  { k: "Inject", v: "A major collision lands. Atlas says allocation is no longer optimal — and moves." },
];

export default function Landing() {
  return (
    <div className="site">
      <div className="aurora" />
      <SiteNav />

      <header className="hero">
        <p className="kicker kicker-pill"><Sparkles size={13} /> ASU AIR · Phoenix / Tempe · Decision support</p>
        <h1>
          See the whole emergency.
          <br />
          <span>Move the right response.</span>
        </h1>
        <p className="lede">
          It fails when too much information arrives too quickly. Atlas uses ASU AIR to process
          thousands of emergency reports in parallel, detect duplicate calls, and continuously
          recommend how limited units should move as the scene changes.
        </p>
        <div className="hero-actions">
          <Link className={buttonClass({ variant: "primary", size: "lg" })} to="/console">
            <Play size={16} fill="currentColor" /> Launch live console
          </Link>
          <Link className={buttonClass({ variant: "outline", size: "lg" })} to="/how-it-works">
            Explain it to judges <ArrowRight size={16} />
          </Link>
        </div>
        <div className="hero-trust"><span className="live-indicator" /> Demo-safe synthetic data <i /> Human approval at every dispatch</div>
        <div className="hero-metrics">
          <Card className="metric-card">
            <strong>2,000</strong>
            <span>calls in a surge</span>
          </Card>
          <Card className="metric-card">
            <strong>127</strong>
            <span>unique emergencies</span>
          </Card>
          <Card className="metric-card">
            <strong>P1–P4</strong>
            <span>human-approved priority</span>
          </Card>
          <Card className="metric-card">
            <strong>AIR</strong>
            <span>ASR · LLM · embeddings</span>
          </Card>
        </div>
      </header>

      <section className="pitch">
        <p className="kicker">20-second pitch</p>
        <blockquote>
          Instead of helping dispatchers handle one call, Atlas helps them understand the entire
          emergency landscape.
        </blockquote>
      </section>

      <section className="split">
        <div>
          <p className="kicker">The problem</p>
          <h2>One dispatcher. A city on fire with 911 audio.</h2>
          <p>
            “There’s smoke coming from an apartment.” “My dad collapsed and isn’t responding.”
            “Three-car crash on Rural and Broadway.” “Someone is yelling outside but I don’t see a
            weapon.”
          </p>
          <p>
            Those four sentences are four different realities — or they might be two. During a major
            event, people call about the same crash from three corners of Mill Ave. Atlas has to
            know.
          </p>
        </div>
        <aside className="incident-card-hero">
          <span className="badge P1">P1</span>
          <h3>Incident #183 · Medical</h3>
          <p>Unconscious person. Possible cardiac arrest. Tempe 85281.</p>
          <dl>
            <div>
              <dt>Recommended</dt>
              <dd>Nearest ALS ambulance</dd>
            </div>
            <div>
              <dt>Cluster</dt>
              <dd>6 related calls</dd>
            </div>
            <div>
              <dt>Confidence</dt>
              <dd>94%</dd>
            </div>
          </dl>
          <p className="fine">Atlas recommends. The dispatcher approves.</p>
        </aside>
      </section>

      <section>
        <p className="kicker">What we built</p>
        <h2>Six AIR-backed capabilities. One live map.</h2>
        <div className="card-grid">
          {capabilities.map((item) => (
            <Card key={item.num} className="glass-card capability-card">
              <CardHeader>
                <span className="capability-icon"><item.icon size={17} /></span>
                <span className="capability-number">{item.num}</span>
                <CardTitle>{item.title}</CardTitle>
              </CardHeader>
              <CardContent><CardDescription>{item.body}</CardDescription></CardContent>
            </Card>
          ))}
        </div>
      </section>

      <section className="demo-strip">
        <div>
          <p className="kicker">The demo</p>
          <h2>Press start. Watch the city resolve.</h2>
          <ol>
            {flow.map((step) => (
              <li key={step.k}>
                <strong>{step.k}</strong>
                <span>{step.v}</span>
              </li>
            ))}
          </ol>
          <Link className={buttonClass({ variant: "primary", size: "lg" })} to="/console">
            Open the operations console <ArrowRight size={16} />
          </Link>
        </div>
      </section>

      <section className="ethics">
        <p className="kicker">Responsible by design</p>
        <h2>Decision support, not an autonomous dispatcher.</h2>
        <p>
          Atlas never closes the loop on its own. Severity, assignment, and reallocation are
          recommendations. A human still owns the radio. That is the product — and it is the ethical
          line this challenge asked for.
        </p>
      </section>

      <SiteFooter />
    </div>
  );
}
