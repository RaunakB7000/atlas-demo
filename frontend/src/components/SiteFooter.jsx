import { Link } from "react-router-dom";
import { ArrowUpRight, RadioTower } from "./ui/icons";

export default function SiteFooter() {
  return (
    <footer className="site-footer">
      <div>
        <strong className="footer-brand"><RadioTower size={15} /> ATLAS</strong>
        <p>AI Emergency Operations Copilot · Built for the ASU AIR / Spark challenge.</p>
      </div>
      <div className="footer-links">
        <Link to="/how-it-works">Architecture <ArrowUpRight size={12} /></Link>
        <Link to="/console">Operations console <ArrowUpRight size={12} /></Link>
      </div>
    </footer>
  );
}
