import { NavLink } from "react-router-dom";
import { ArrowUpRight, RadioTower } from "./ui/icons";
import { buttonClass } from "./ui/Button";

export default function SiteNav({ compact = false }) {
  return (
    <nav className={`site-nav ${compact ? "compact" : ""}`}>
      <NavLink to="/" className="brand">
        <span className="brand-mark"><RadioTower size={13} strokeWidth={2.2} /></span>
        <span className="brand-copy"><strong>ATLAS</strong><small>Emergency operations</small></span>
      </NavLink>
      <div className="nav-links">
        <NavLink to="/how-it-works">How it works</NavLink>
        <NavLink to="/console">Live console</NavLink>
        <NavLink to="/console" className={buttonClass({ variant: "primary", size: "sm", className: "nav-cta" })}>
          Start the demo <ArrowUpRight size={14} />
        </NavLink>
      </div>
    </nav>
  );
}
