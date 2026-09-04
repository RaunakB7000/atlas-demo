function cn(...values) {
  return values.filter(Boolean).join(" ");
}

export function Card({ className = "", ...props }) {
  return <div data-slot="card" className={cn("ui-card", className)} {...props} />;
}

export function CardHeader({ className = "", ...props }) {
  return <div data-slot="card-header" className={cn("ui-card-header", className)} {...props} />;
}

export function CardTitle({ className = "", ...props }) {
  return <h3 data-slot="card-title" className={cn("ui-card-title", className)} {...props} />;
}

export function CardDescription({ className = "", ...props }) {
  return <p data-slot="card-description" className={cn("ui-card-description", className)} {...props} />;
}

export function CardContent({ className = "", ...props }) {
  return <div data-slot="card-content" className={cn("ui-card-content", className)} {...props} />;
}

export function CardFooter({ className = "", ...props }) {
  return <div data-slot="card-footer" className={cn("ui-card-footer", className)} {...props} />;
}
