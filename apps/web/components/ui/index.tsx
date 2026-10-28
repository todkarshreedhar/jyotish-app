"use client";

// Shared component kit (US-05). Every screen builds from these.

import Link from "next/link";
import { forwardRef, useId, useState, type ButtonHTMLAttributes, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes } from "react";

function cx(...c: (string | false | null | undefined)[]) {
  return c.filter(Boolean).join(" ");
}

type BtnVariant = "primary" | "secondary" | "ghost" | "danger";
const btn: Record<BtnVariant, string> = {
  primary: "bg-primary text-primary-text hover:opacity-90",
  secondary: "border border-border bg-surface text-text hover:bg-surface-2",
  ghost: "text-text hover:bg-surface-2",
  danger: "bg-danger text-white hover:opacity-90",
};

export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & { variant?: BtnVariant; busy?: boolean }>(
  function Button({ variant = "primary", busy, className, children, disabled, ...rest }, ref) {
    return (
      <button
        ref={ref}
        className={cx("inline-flex min-h-11 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50", btn[variant], className)}
        disabled={disabled || busy}
        aria-busy={busy || undefined}
        {...rest}
      >
        {busy && <Spinner small />}
        {children}
      </button>
    );
  },
);

export function ButtonLink({ href, variant = "primary", className, children }: { href: string; variant?: BtnVariant; className?: string; children: ReactNode }) {
  return (
    <Link href={href} className={cx("inline-flex min-h-11 items-center justify-center rounded-lg px-4 py-2 text-sm font-semibold", btn[variant], className)}>
      {children}
    </Link>
  );
}

export function Card({ children, className, title, actions }: { children: ReactNode; className?: string; title?: ReactNode; actions?: ReactNode }) {
  return (
    <section className={cx("rounded-xl border border-border bg-surface p-4 shadow-sm sm:p-5", className)}>
      {(title || actions) && (
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          {title && <h2 className="text-lg font-semibold">{title}</h2>}
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}

export function Field({ label, hint, error, children, htmlFor }: { label: ReactNode; hint?: ReactNode; error?: string; children: ReactNode; htmlFor: string }) {
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={htmlFor} className="text-sm font-medium">{label}</label>
      {children}
      {hint && !error && <p id={`${htmlFor}-hint`} className="text-xs text-muted">{hint}</p>}
      {error && <p id={`${htmlFor}-error`} role="alert" className="text-sm text-danger">{error}</p>}
    </div>
  );
}

const inputCls = "min-h-11 w-full rounded-lg border border-border bg-surface px-3 py-2 text-base text-text placeholder:text-muted";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement> & { invalid?: boolean }>(function Input({ className, invalid, ...rest }, ref) {
  return <input ref={ref} className={cx(inputCls, invalid && "border-danger", className)} aria-invalid={invalid || undefined} {...rest} />;
});

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(function Select({ className, ...rest }, ref) {
  return <select ref={ref} className={cx(inputCls, className)} {...rest} />;
});

export function Spinner({ small, label }: { small?: boolean; label?: string }) {
  return (
    <span role={label ? "status" : undefined} className="inline-flex items-center gap-2">
      <span className={cx("inline-block animate-spin rounded-full border-2 border-current border-t-transparent", small ? "h-4 w-4" : "h-6 w-6")} aria-hidden />
      {label && <span className="text-sm text-muted">{label}</span>}
    </span>
  );
}

export function Alert({ kind = "info", children }: { kind?: "info" | "error" | "ok" | "warn"; children: ReactNode }) {
  const cls = { info: "border-border bg-surface-2", error: "border-danger text-danger", ok: "border-ok", warn: "border-accent bg-surface-2" }[kind];
  return (
    <div role={kind === "error" ? "alert" : "status"} className={cx("rounded-lg border-l-4 p-3 text-sm", cls)}>
      {children}
    </div>
  );
}

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "accent" | "danger" | "ok" }) {
  const cls = { neutral: "bg-surface-2 text-muted", accent: "bg-accent/20 text-text", danger: "bg-danger/15 text-danger", ok: "bg-ok/15 text-ok" }[tone];
  return <span className={cx("inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium", cls)}>{children}</span>;
}

export function Tabs<T extends string>({ tabs, value, onChange, label }: { tabs: { id: T; label: ReactNode }[]; value: T; onChange: (v: T) => void; label: string }) {
  return (
    <div role="tablist" aria-label={label} className="flex gap-1 overflow-x-auto border-b border-border">
      {tabs.map((t) => (
        <button
          key={t.id}
          role="tab"
          id={`tab-${t.id}`}
          aria-selected={value === t.id}
          aria-controls={`panel-${t.id}`}
          tabIndex={value === t.id ? 0 : -1}
          onClick={() => onChange(t.id)}
          onKeyDown={(e) => {
            const i = tabs.findIndex((x) => x.id === value);
            if (e.key === "ArrowRight") onChange(tabs[(i + 1) % tabs.length].id);
            if (e.key === "ArrowLeft") onChange(tabs[(i - 1 + tabs.length) % tabs.length].id);
          }}
          className={cx("min-h-11 whitespace-nowrap border-b-2 px-3 text-sm font-medium", value === t.id ? "border-primary text-primary" : "border-transparent text-muted hover:text-text")}
        >
          {t.label}
        </button>
      ))}
    </div>
  );
}

/** A Jyotish term with a one-line explanation on tap or focus (US-30). */
export function Term({ children, meaning }: { children: ReactNode; meaning: string }) {
  const [open, setOpen] = useState(false);
  const id = useId();
  return (
    <span className="relative inline-block">
      <button
        type="button"
        className="cursor-help underline decoration-dotted underline-offset-4"
        aria-describedby={open ? id : undefined}
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
        onBlur={() => setOpen(false)}
        onKeyDown={(e) => e.key === "Escape" && setOpen(false)}
      >
        {children}
      </button>
      {open && (
        <span id={id} role="tooltip" className="absolute left-0 top-full z-20 mt-1 w-64 rounded-lg border border-border bg-surface p-2 text-xs font-normal text-text shadow-lg">
          {meaning}
        </span>
      )}
    </span>
  );
}

export function Table({ children, caption }: { children: ReactNode; caption?: string }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] border-collapse text-sm [&_td]:border-b [&_td]:border-border [&_td]:px-2 [&_td]:py-2 [&_th]:border-b [&_th]:border-border [&_th]:bg-surface-2 [&_th]:px-2 [&_th]:py-2 [&_th]:text-left [&_th]:font-semibold">
        {caption && <caption className="sr-only">{caption}</caption>}
        {children}
      </table>
    </div>
  );
}

export { cx };
