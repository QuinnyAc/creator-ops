import type { ReactNode } from "react";

export function PageHeader({
  eyebrow,
  title,
  description,
  action,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="pageHeader">
      <div>
        {eyebrow ? <span className="eyebrow">{eyebrow}</span> : null}
        <h1>{title}</h1>
        {description ? <p>{description}</p> : null}
      </div>
      {action ? <div className="pageHeaderAction">{action}</div> : null}
    </div>
  );
}

export function StatCard({
  label,
  value,
  hint,
}: {
  label: string;
  value: ReactNode;
  hint?: string;
}) {
  return (
    <div className="statCard">
      <span>{label}</span>
      <strong>{value}</strong>
      {hint ? <small>{hint}</small> : null}
    </div>
  );
}

export function Section({
  title,
  description,
  children,
  action,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <section className="sectionCard">
      <div className="sectionHeading">
        <div>
          <h2>{title}</h2>
          {description ? <p>{description}</p> : null}
        </div>
        {action}
      </div>
      {children}
    </section>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="emptyState">{children}</div>;
}

export function Badge({ value }: { value: string }) {
  return <span className={`badge badge-${value.replaceAll("_", "-")}`}>{value.replaceAll("_", " ")}</span>;
}

export function LoadingBlock() {
  return <div className="loadingBlock">正在读取 Creator Ops 数据…</div>;
}

export function ErrorBanner({ message }: { message: string }) {
  return <div className="errorBanner">{message}</div>;
}

export function formatNumber(value: number) {
  return new Intl.NumberFormat("zh-CN", { notation: value >= 10000 ? "compact" : "standard" }).format(value);
}

export function formatDate(value: string | null) {
  if (!value) return "—";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}
