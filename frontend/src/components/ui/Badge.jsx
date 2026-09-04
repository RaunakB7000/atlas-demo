function cn(...values) {
  return values.filter(Boolean).join(" ");
}

export default function Badge({ variant = "default", className = "", ...props }) {
  return (
    <span
      data-slot="badge"
      data-variant={variant}
      className={cn("ui-badge", `ui-badge-${variant}`, className)}
      {...props}
    />
  );
}
