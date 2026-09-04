function cn(...values) {
  return values.filter(Boolean).join(" ");
}

export function buttonClass({ variant = "default", size = "default", className = "" } = {}) {
  return cn("ui-button", `ui-button-${variant}`, `ui-button-${size}`, className);
}

export default function Button({
  variant = "default",
  size = "default",
  className = "",
  type = "button",
  ...props
}) {
  return (
    <button
      type={type}
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={buttonClass({ variant, size, className })}
      {...props}
    />
  );
}
