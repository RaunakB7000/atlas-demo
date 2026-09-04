import { Navigate, Route, Routes } from "react-router-dom";
import Console from "./pages/Console";
import HowItWorks from "./pages/HowItWorks";
import Landing from "./pages/Landing";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/how-it-works" element={<HowItWorks />} />
      <Route path="/console" element={<Console />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
