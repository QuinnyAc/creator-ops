"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import {
  CalendarIcon,
  ChartIcon,
  HomeIcon,
  PipelineIcon,
  ReviewIcon,
  SettingsIcon,
  SparkIcon,
  TopicIcon,
} from "@/components/icons";
import { clearAccessToken, getAccessToken } from "@/lib/auth";

const nav = [
  { href: "/", label: "Dashboard", icon: HomeIcon },
  { href: "/inspirations", label: "灵感 Inbox", icon: SparkIcon },
  { href: "/topics", label: "选题库", icon: TopicIcon },
  { href: "/content", label: "内容 Pipeline", icon: PipelineIcon },
  { href: "/publishing", label: "发布管理", icon: CalendarIcon },
  { href: "/publishing/data", label: "单视频数据", icon: ChartIcon },
  { href: "/analytics", label: "数据分析", icon: ChartIcon },
  { href: "/analytics/titles", label: "标题分析", icon: ChartIcon },
  { href: "/reviews", label: "内容复盘", icon: ReviewIcon },
  { href: "/insights", label: "Creator Playbook", icon: SparkIcon },
  { href: "/settings", label: "设置", icon: SettingsIcon },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const [authenticated, setAuthenticated] = useState(false);
  const requireAuth = process.env.NEXT_PUBLIC_REQUIRE_AUTH === "true";

  useEffect(() => {
    const hasToken = Boolean(getAccessToken());
    setAuthenticated(hasToken);
    if (requireAuth && !hasToken && pathname !== "/login") {
      window.location.assign("/login");
    }
  }, [pathname, requireAuth]);

  if (pathname === "/login") {
    return (
      <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 24, background: "var(--bg)" }}>
        {children}
      </main>
    );
  }

  function logout() {
    clearAccessToken();
    setAuthenticated(false);
    window.location.assign("/login");
  }

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brandMark">CO</div>
          <div>
            <strong>Quinny的工作台</strong>
            <span>自媒体运营平台</span>
          </div>
        </div>
        <nav className="nav">
          {nav.map(({ href, label, icon: Icon }) => {
            const active = href === "/" || href === "/analytics" || href === "/publishing"
              ? pathname === href
              : pathname.startsWith(href);
            return (
              <Link key={href} className={`navItem ${active ? "active" : ""}`} href={href}>
                <Icon />
                <span>{label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="sidebarFooter">
          <span className="statusDot" />
          {authenticated ? "Workplace" : "Local MVP workspace"}
        </div>
      </aside>
      <main className="workspace">
        <header className="topbar">
          <div>
            <span className="eyebrow">CREATOR OPERATIONS</span>
            <strong>把每一次创作变成可复用的增长经验</strong>
          </div>
          <div className="creatorChip">
            <span>C</span>
            {authenticated ? (
              <button
                type="button"
                onClick={logout}
                style={{ border: 0, background: "transparent", padding: 0, color: "inherit", fontSize: 12 }}
              >
                退出
              </button>
            ) : (
              <Link href="/login">登录</Link>
            )}
          </div>
        </header>
        <div className="page">{children}</div>
      </main>
    </div>
  );
}
