"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import { useParams } from "next/navigation";

import {
  EmptyState,
  ErrorBanner,
  LoadingBlock,
  PageHeader,
  Section,
  StatCard,
  formatDate,
  formatNumber,
} from "@/components/ui";
import { api, postJson } from "@/lib/api";
import type {
  ContentItem,
  MetricSnapshot,
  PerformanceMilestone,
  Platform,
  PlatformAccount,
  Publication,
} from "@/lib/types";

function numberValue(value: string) {
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) && parsed >= 0 ? Math.floor(parsed) : 0;
}

function TrendChart({ snapshots }: { snapshots: MetricSnapshot[] }) {
  const ordered = [...snapshots].reverse();
  if (ordered.length === 0) {
    return <EmptyState>还没有数据快照。记录第一组数据后，这里会形成播放量变化曲线。</EmptyState>;
  }

  const width = 720;
  const height = 220;
  const paddingX = 36;
  const paddingY = 28;
  const maxViews = Math.max(1, ...ordered.map((item) => item.views));
  const usableWidth = width - paddingX * 2;
  const usableHeight = height - paddingY * 2;
  const points = ordered.map((item, index) => {
    const x = paddingX + (ordered.length === 1 ? usableWidth / 2 : (index / (ordered.length - 1)) * usableWidth);
    const y = paddingY + usableHeight - (item.views / maxViews) * usableHeight;
    return `${x},${y}`;
  });

  return (
    <div style={{ overflowX: "auto" }}>
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="播放量变化趋势" style={{ width: "100%", minWidth: 620, display: "block" }}>
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const y = paddingY + usableHeight - ratio * usableHeight;
          return (
            <g key={ratio}>
              <line x1={paddingX} y1={y} x2={width - paddingX} y2={y} stroke="var(--line)" strokeWidth="1" />
              <text x="4" y={y + 4} fontSize="10" fill="var(--muted)">{formatNumber(Math.round(maxViews * ratio))}</text>
            </g>
          );
        })}
        <polyline points={points.join(" ")} fill="none" stroke="var(--accent)" strokeWidth="3" strokeLinejoin="round" strokeLinecap="round" />
        {points.map((point, index) => {
          const [x, y] = point.split(",").map(Number);
          return <circle key={`${point}-${index}`} cx={x} cy={y} r="4" fill="var(--accent)" />;
        })}
      </svg>
      <div className="dataRowMeta" style={{ marginTop: 6 }}>
        共 {ordered.length} 个数据快照 · 曲线按记录时间从左到右展示播放量变化
      </div>
    </div>
  );
}

export default function PublicationDetailPage() {
  const params = useParams<{ id: string }>();
  const publicationId = params.id;
  const [publication, setPublication] = useState<Publication | null>(null);
  const [account, setAccount] = useState<PlatformAccount | null>(null);
  const [platform, setPlatform] = useState<Platform | null>(null);
  const [content, setContent] = useState<ContentItem | null>(null);
  const [snapshots, setSnapshots] = useState<MetricSnapshot[]>([]);
  const [milestones, setMilestones] = useState<PerformanceMilestone[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const [views, setViews] = useState("");
  const [likes, setLikes] = useState("");
  const [comments, setComments] = useState("");
  const [favorites, setFavorites] = useState("");
  const [shares, setShares] = useState("");

  const refreshMetrics = useCallback(async () => {
    if (!publicationId) return;
    const [nextSnapshots, nextMilestones] = await Promise.all([
      api<MetricSnapshot[]>(`/analytics/publications/${publicationId}/metrics`),
      api<PerformanceMilestone[]>(`/analytics/publications/${publicationId}/milestones`),
    ]);
    setSnapshots(nextSnapshots);
    setMilestones(nextMilestones);
  }, [publicationId]);

  const load = useCallback(async () => {
    if (!publicationId) return;
    setError("");
    try {
      const [nextPublication, accounts, platforms, contents, nextSnapshots, nextMilestones] = await Promise.all([
        api<Publication>(`/publications/${publicationId}`),
        api<PlatformAccount[]>("/platform-accounts"),
        api<Platform[]>("/platforms"),
        api<ContentItem[]>("/contents"),
        api<MetricSnapshot[]>(`/analytics/publications/${publicationId}/metrics`),
        api<PerformanceMilestone[]>(`/analytics/publications/${publicationId}/milestones`),
      ]);
      const nextAccount = accounts.find((item) => item.id === nextPublication.platform_account_id) ?? null;
      const nextPlatform = nextAccount ? platforms.find((item) => item.id === nextAccount.platform_id) ?? null : null;
      const nextContent = contents.find((item) => item.id === nextPublication.content_id) ?? null;
      setPublication(nextPublication);
      setAccount(nextAccount);
      setPlatform(nextPlatform);
      setContent(nextContent);
      setSnapshots(nextSnapshots);
      setMilestones(nextMilestones);

      const latest = nextSnapshots[0];
      if (latest) {
        setViews(String(latest.views));
        setLikes(String(latest.likes));
        setComments(String(latest.comments));
        setFavorites(String(latest.favorites));
        setShares(String(latest.shares));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "单个作品数据加载失败");
    } finally {
      setLoading(false);
    }
  }, [publicationId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      void refreshMetrics().catch(() => undefined);
    }, 20_000);
    return () => window.clearInterval(timer);
  }, [refreshMetrics]);

  const latest = snapshots[0];
  const engagementRate = useMemo(() => {
    if (!latest?.views) return 0;
    return ((latest.likes + latest.comments + latest.favorites + latest.shares) / latest.views) * 100;
  }, [latest]);

  async function addSnapshot(event: FormEvent) {
    event.preventDefault();
    if (!publicationId) return;
    setSaving(true);
    setError("");
    try {
      await postJson<MetricSnapshot>(`/analytics/publications/${publicationId}/metrics`, {
        captured_at: new Date().toISOString(),
        views: numberValue(views),
        likes: numberValue(likes),
        comments: numberValue(comments),
        favorites: numberValue(favorites),
        shares: numberValue(shares),
        followers_gained: 0,
        extra_metrics: { source: "manual", platform: platform?.slug ?? "unknown" },
      });
      await refreshMetrics();
    } catch (err) {
      setError(err instanceof Error ? err.message : "数据快照保存失败");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingBlock />;

  return (
    <>
      <PageHeader
        eyebrow="VIDEO PERFORMANCE"
        title={publication?.title || content?.title || "单个作品数据"}
        description={`${platform?.name ?? "平台"} · ${account?.name ?? "账号"} · 发布于 ${formatDate(publication?.published_at ?? publication?.scheduled_at ?? null)}`}
        action={<Link className="button small secondary" href="/publishing">← 返回发布管理</Link>}
      />
      {error ? <ErrorBanner message={error} /> : null}

      <div className="statsGrid">
        <StatCard label="播放" value={latest ? formatNumber(latest.views) : "—"} hint={latest ? `更新 ${formatDate(latest.captured_at)}` : "暂无快照"} />
        <StatCard label="点赞" value={latest ? formatNumber(latest.likes) : "—"} />
        <StatCard label="评论" value={latest ? formatNumber(latest.comments) : "—"} />
        <StatCard label="收藏" value={latest ? formatNumber(latest.favorites) : "—"} />
        <StatCard label="互动率" value={latest ? `${engagementRate.toFixed(2)}%` : "—"} hint="点赞+评论+收藏+分享 ÷ 播放" />
      </div>

      <Section
        title="作品链接"
        description="从这里可以直接打开平台原作品。"
        action={publication?.url ? <a className="button small secondary" href={publication.url} target="_blank" rel="noreferrer">打开作品 ↗</a> : undefined}
      >
        <div className="dataRowMeta" style={{ wordBreak: "break-all" }}>{publication?.url || "还没有填写已发布作品链接。"}</div>
      </Section>

      <div style={{ height: 16 }} />

      <Section title="播放量变化" description="每次手动记录或未来平台自动同步，都会形成一个新的历史快照。">
        <TrendChart snapshots={snapshots} />
      </Section>

      <div style={{ height: 16 }} />

      <Section title="关键时间节点" description="自动匹配发布后 24 小时、72 小时、7 天、30 天之后的第一条数据快照。">
        <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 10, overflowX: "auto" }}>
          {milestones.map((item) => (
            <div className="metricBox" key={item.label} style={{ minWidth: 150, alignItems: "flex-start" }}>
              <span>{item.label}</span>
              <strong>{item.views === null ? "待记录" : `${formatNumber(item.views)} 播放`}</strong>
              <small className="dataRowMeta">点赞 {item.likes === null ? "—" : formatNumber(item.likes)} · 收藏 {item.favorites === null ? "—" : formatNumber(item.favorites)}</small>
              <small className="dataRowMeta">目标 {formatDate(item.target_at)}</small>
            </div>
          ))}
        </div>
      </Section>

      <div style={{ height: 16 }} />

      <Section title="记录当前平台数据" description="小红书和哔哩哔哩官方数据授权接通前，可把平台后台当前数字录入。保存后立即进入趋势、节点和数据分析。">
        <form className="formGrid" onSubmit={addSnapshot}>
          <div className="field"><label htmlFor="metric-views">播放</label><input id="metric-views" className="input" type="number" min="0" value={views} onChange={(e) => setViews(e.target.value)} placeholder="0" /></div>
          <div className="field"><label htmlFor="metric-likes">点赞</label><input id="metric-likes" className="input" type="number" min="0" value={likes} onChange={(e) => setLikes(e.target.value)} placeholder="0" /></div>
          <div className="field"><label htmlFor="metric-comments">评论</label><input id="metric-comments" className="input" type="number" min="0" value={comments} onChange={(e) => setComments(e.target.value)} placeholder="0" /></div>
          <div className="field"><label htmlFor="metric-favorites">收藏</label><input id="metric-favorites" className="input" type="number" min="0" value={favorites} onChange={(e) => setFavorites(e.target.value)} placeholder="0" /></div>
          <div className="field"><label htmlFor="metric-shares">分享</label><input id="metric-shares" className="input" type="number" min="0" value={shares} onChange={(e) => setShares(e.target.value)} placeholder="0" /></div>
          <div className="formActions"><button className="button" type="submit" disabled={saving}>{saving ? "保存中…" : "保存当前数据"}</button></div>
        </form>
      </Section>

      <div style={{ height: 16 }} />

      <Section title={`历史数据快照 · ${snapshots.length}`} description="最新记录在最上方，可用于判断作品后续是否继续获得流量。">
        {snapshots.length === 0 ? (
          <EmptyState>还没有历史数据。</EmptyState>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: 720 }}>
              <thead>
                <tr style={{ textAlign: "left", borderBottom: "1px solid var(--line)" }}>
                  {['记录时间', '播放', '点赞', '评论', '收藏', '分享'].map((label) => <th key={label} style={{ padding: "10px 8px", fontSize: 11 }}>{label}</th>)}
                </tr>
              </thead>
              <tbody>
                {snapshots.map((item) => (
                  <tr key={item.id} style={{ borderBottom: "1px solid var(--line)" }}>
                    <td style={{ padding: "10px 8px", fontSize: 12 }}>{formatDate(item.captured_at)}</td>
                    <td style={{ padding: "10px 8px", fontWeight: 700 }}>{formatNumber(item.views)}</td>
                    <td style={{ padding: "10px 8px" }}>{formatNumber(item.likes)}</td>
                    <td style={{ padding: "10px 8px" }}>{formatNumber(item.comments)}</td>
                    <td style={{ padding: "10px 8px" }}>{formatNumber(item.favorites)}</td>
                    <td style={{ padding: "10px 8px" }}>{formatNumber(item.shares)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>
    </>
  );
}
