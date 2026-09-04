import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, Sparkles } from "../components/ui/icons";
import SiteFooter from "../components/SiteFooter";
import SiteNav from "../components/SiteNav";
import Badge from "../components/ui/Badge";
import { buttonClass } from "../components/ui/Button";
import { Card } from "../components/ui/Card";

const agents = [
  {
    name: "Call Understanding",
    air: "AIR LLM",
    does: "Turns unstructured 911 text into type, injuries, hazards, people count, and an address hint.",
  },
  {
    name: "Severity",
    air: "AIR LLM",
    does: "Recommends P1–P4 with a rationale. Escalation is advice, never a silent action.",
  },
  {
    name: "Clustering",
    air: "AIR embeddings",
    does: "Merges duplicate reports using geographic proximity, time proximity, and semantic similarity.",
  },
  {
    name: "Allocation",
    air: "Optimization",
    does: "Picks units from severity, required equipment, nearby availability, and hospital load.",
  },
  {
    name: "Routing",
    air: "Travel model",
    does: "Estimates ETA with traffic and closure penalties so the closest capable unit wins.",
  },
  {
    name: "Prediction",
    air: "Spatiotemporal",
    does: "Reads historical synthetic volume and stages units before Friday night on Mill Ave.",
  },
];

const stack = [
  ["Frontend", "React + Vite + MapTiler"],
  ["Backend", "Python / FastAPI"],
  ["Database", "SQLite"],
  ["Models", "ASU AIR · Qwen ASR · embeddings · reasoning"],
  ["Data", "Synthetic Tempe / Phoenix 911 only"],
];

export default function HowItWorks() {
  return (
    <div className="site">
      <div className="aurora" />
      <SiteNav />

      <header className="hero slim">
        <p className="kicker kicker-pill"><Sparkles size={13} /> Architecture for judges</p>
        <h1>Not “we called an LLM.” We process the surge.</h1>
        <p className="lede">
          AIR’s justification is compute: concurrent transcription, structured extraction, and
          embedding-based clustering across hundreds of reports while the map keeps moving.
        </p>
        <Link className={buttonClass({ variant: "primary", size: "lg" })} to="/console">
          See it running <ArrowRight size={16} />
        </Link>
      </header>

      <section>
        <p className="kicker">Pipeline</p>
        <div className="pipeline">
          {["911 / traffic / weather", "AIR ASR", "Transcript agents", "Optimization", "Live map"].map(
            (step, index) => (
              <Card key={step} className="pipe-step">
                <span>0{index + 1}</span>
                <strong>{step}</strong>
              </Card>
            )
          )}
        </div>
      </section>

      <section>
        <p className="kicker">AIR agent layer</p>
        <h2>Six specialists, one re-plan loop.</h2>
        <div className="agent-list">
          {agents.map((agent) => (
            <article key={agent.name} className="agent-card">
              <div>
                <h3>{agent.name}</h3>
                <Badge variant="secondary">{agent.air}</Badge>
              </div>
              <p>{agent.does}</p>
              <CheckCircle2 className="agent-check" size={17} />
            </article>
          ))}
        </div>
      </section>

      <section className="split">
        <div>
          <p className="kicker">The wow moment</p>
          <h2>Allocation is no longer optimal. Recalculating…</h2>
          <p>
            Mid-demo we inject a major collision. Atlas does not append a pin and wait. It looks at
            units already en route to lower-priority scenes and diverts the one that can save the
            most time.
          </p>
          <p>That loop — observe, analyze, plan, recommend, new information, re-plan — is the product.</p>
        </div>
        <aside className="glass-card">
          <p className="kicker">Stack</p>
          <dl className="stack-list">
            {stack.map(([k, v]) => (
              <div key={k}>
                <dt>{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
        </aside>
      </section>

      <SiteFooter />
    </div>
  );
}
