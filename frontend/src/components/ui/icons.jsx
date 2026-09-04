function Icon({ children, size = 16, ...props }) {
  return (
    <svg
      aria-hidden="true"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      {children}
    </svg>
  );
}

export const Activity = (props) => <Icon {...props}><path d="M3 12h4l2.5-7 5 14 2.5-7h4" /></Icon>;
export const ArrowRight = (props) => <Icon {...props}><path d="M5 12h14M13 6l6 6-6 6" /></Icon>;
export const ArrowLeft = (props) => <Icon {...props}><path d="M19 12H5m6-6-6 6 6 6" /></Icon>;
export const ArrowUpRight = (props) => <Icon {...props}><path d="M7 17 17 7M8 7h9v9" /></Icon>;
export const Check = (props) => <Icon {...props}><path d="m5 12 4 4L19 6" /></Icon>;
export const CheckCircle2 = (props) => <Icon {...props}><circle cx="12" cy="12" r="9" /><path d="m8 12 3 3 5-6" /></Icon>;
export const ChevronDown = (props) => <Icon {...props}><path d="m6 9 6 6 6-6" /></Icon>;
export const Download = (props) => <Icon {...props}><path d="M12 3v12m-5-5 5 5 5-5M5 20h14" /></Icon>;
export const ExternalLink = (props) => <Icon {...props}><path d="M14 5h5v5M10 14l9-9M19 13v6H5V5h6" /></Icon>;
export const GitMerge = (props) => <Icon {...props}><circle cx="6" cy="5" r="2" /><circle cx="18" cy="6" r="2" /><circle cx="6" cy="19" r="2" /><path d="M6 7v10M8 9c5 0 6-3 8-3" /></Icon>;
export const Play = (props) => <Icon {...props}><path d="m8 5 11 7-11 7Z" /></Icon>;
export const Radar = (props) => <Icon {...props}><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><path d="M12 12 18 6M12 3v2" /></Icon>;
export const RefreshCw = (props) => <Icon {...props}><path d="M20 7v5h-5M4 17v-5h5M6.2 8a7 7 0 0 1 11.2-1.6L20 12M4 12l2.6 5.6A7 7 0 0 0 17.8 16" /></Icon>;
export const RefreshCcw = RefreshCw;
export const Route = (props) => <Icon {...props}><circle cx="6" cy="18" r="2" /><circle cx="18" cy="6" r="2" /><path d="M8 18h2a4 4 0 0 0 4-4v-4a4 4 0 0 1 4-4" /></Icon>;
export const ShieldCheck = (props) => <Icon {...props}><path d="M12 3 4 6v5c0 5 3.5 8.3 8 10 4.5-1.7 8-5 8-10V6Z" /><path d="m8.5 12 2.2 2.2 4.8-5" /></Icon>;
export const ShieldAlert = (props) => <Icon {...props}><path d="M12 3 4 6v5c0 5 3.5 8.3 8 10 4.5-1.7 8-5 8-10V6Z" /><path d="M12 8v5M12 16h.01" /></Icon>;
export const Sparkles = (props) => <Icon {...props}><path d="m12 3 1.2 3.2L16 7.5l-2.8 1.3L12 12l-1.2-3.2L8 7.5l2.8-1.3ZM18 14l.8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8ZM5 12l.7 1.8L7.5 15l-1.8.7L5 17.5l-.7-1.8L2.5 15l1.8-1.2Z" /></Icon>;
export const RadioTower = (props) => <Icon {...props}><circle cx="12" cy="12" r="2" /><path d="M8.5 8.5a5 5 0 0 0 0 7M15.5 8.5a5 5 0 0 1 0 7M5.5 5.5a9 9 0 0 0 0 13M18.5 5.5a9 9 0 0 1 0 13" /></Icon>;
export const FileChartColumn = (props) => <Icon {...props}><path d="M6 3h9l4 4v14H6Z" /><path d="M14 3v5h5M9 17v-3M12 17v-6M15 17v-4" /></Icon>;
export const Pause = (props) => <Icon {...props}><path d="M9 6v12M15 6v12" /></Icon>;
export const Radio = (props) => <Icon {...props}><circle cx="12" cy="12" r="2" /><path d="M7.8 7.8a6 6 0 0 0 0 8.4M16.2 7.8a6 6 0 0 1 0 8.4" /></Icon>;
export const AlertTriangle = (props) => <Icon {...props}><path d="m12 3 10 18H2Z" /><path d="M12 9v5M12 17h.01" /></Icon>;
export const Gauge = (props) => <Icon {...props}><path d="M4 18a8 8 0 1 1 16 0M12 14l4-4M7 18h10" /></Icon>;
export const Layers3 = (props) => <Icon {...props}><path d="m12 3 9 5-9 5-9-5ZM3 12l9 5 9-5M3 16l9 5 9-5" /></Icon>;
export const Siren = (props) => <Icon {...props}><path d="M7 16v-5a5 5 0 0 1 10 0v5M5 20h14M4 12H2M22 12h-2M5 5l-2-2M19 5l2-2" /></Icon>;
export const X = (props) => <Icon {...props}><path d="m6 6 12 12M18 6 6 18" /></Icon>;
export const Send = (props) => <Icon {...props}><path d="m3 11 18-8-8 18-2-8ZM11 13l4-4" /></Icon>;
export const Search = (props) => <Icon {...props}><circle cx="11" cy="11" r="7" /><path d="m20 20-4-4" /></Icon>;
export const ListFilter = (props) => <Icon {...props}><path d="M4 6h16M7 12h10M10 18h4" /></Icon>;
