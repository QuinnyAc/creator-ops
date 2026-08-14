"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { EmptyState, ErrorBanner, PageHeader, Section, StatCard, formatDate, formatNumber } from "@/components/ui";
import { api, postJson } from "@/lib/api";
import type {
  AnalyticsSummary,
  ContentItem,
  MetricSnapshot,
  PerformanceMilestone,
  PillarAnalyticsItem,
  PillarTrendItem,
  PlatformAnalyticsItem,
  Publication,
} from "@/lib/types";

const TREND_LABELS: Record<PillarTrendItem["signal"], string> = {
  rising: "上升",
  stable: "稳定",
  falling: "下降",
  new: "新方向",
  insufficient: "数据不足",
};

function localNow() {
  const date = new Date();
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000).toISOString().slice(0, 16);
}

const EMPTY_SUMMARY: AnalyticsSummary = {
  publications: 0,
  views: 0,
  likes: 0,
  comments: 0,
  favorites: 0,
  shares: 0,
  followers_gained: 0,
  engagement_rate: 0,
};

export default function AnalyticsPage() {
  const [summary, setSummary] = useState(EMPTY_SUMMARY);
  const [pillarAnalytics, setPillarAnalytics] = useState<PillarAnalyticsItem[]>([]);
  const [pillarTrends, setPillarTrends] = useState<PillarTrendItem[]>([]);
  const [platformAnalytics, setPlatformAnalytics] = useState<PlatformAnalyticsItem[]>([]);
  const [publications, setPublications] = useState<Publication[]>([]);
  const [contents, setContents] = useState<ContentItem[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [metrics, setMetrics] = useState<MetricSnapshot[]>([]);
  const [milestones, setMilestones] = useState<PerformanceMilestone[]>([]);
  const [capturedAt, setCapturedAt] = useState(localNow());
  const [views, setViews] = useState("0");
  const [likes, setLikes] = useState("0");
  const [favorites, setFavorites] = useState("0");
  const [comments, setComments] = useState("0");
  const [shares, setShares] = useState("0");
  const [followers, setFollowers] = useState("0");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const loadOverview = useCallback(async () => {
    try {
      const [nextSummary, nextPillars, nextTrends, nextPlatforms, nextPublications, nextContents] = await Promise.all([
        api<AnalyticsSummary>("/analytics/summary"),
        api<PillarAnalyticsItem[]>("/analytics/pillars"),
        api<PillarTrendItem[]>("/analytics/pillar-trends?window_days=30"),
        api<PlatformAnalyticsItem[]>("/analytics/platforms"),
        api<Publication[]>("/publications"),
        api<ContentItem[]>("/contents"),
      ]);
      setSummary(nextSummary);
      setPillarAnalytics(nextPillars);
      setPillarTrends(nextTrends);
      setPlatformAnalytics(nextPlatforms);
      setPublications(nextPublications);
      setContents(nextContents);
      setSelectedId((current) => current || nextPublications[0]?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "分析数据加载失败");
    }
  }, []);

  const loadPublicationAnalytics = useCallback(async (publicationId: string) => {
    if (!publicationId) {
      setMetrics([]);
      setMilestones([]);
      return;
    }
    try {
      const [nextMetrics, nextMilestones] = await Promise.all([
        api<MetricSnapshot[]>(`/analytics/publications/${publicationId}/metrics`),
        api<PerformanceMilestone[]>(`/analytics/publications/${publicationId}/milestones`),
      ]);
      setMetrics(nextMetrics);
      setMilestones(nextMilestones);
    } catch (err) {
      setError(err instanceof Error ? err.message : "发布表现加载失败");
    }
  }, []);

  useEffect(() => {
    void loadOverview();
  }, [loadOverview]);

  useEffect(() => {
    void loadPublicationAnalytics(selectedId);
  }, [selectedId, loadPublicationAnalytics]);

  const contentMap = useMemo(() => new Map(contents.map((item) => [item.id, item])), [contents]);
  const selectedPublication = publications.find((item) => item.id === selectedId);
  const latest = metrics[0];

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!selectedId) return;
    setSaving(true);
    setError("");
    try {
      await postJson<MetricSnapshot>(`/analytics/publications/${selectedId}/metrics`, {
        captured_at: new Date(capturedAt).toISOString(),
        views: Number(views) || 0,
        likes: Number(likes) || 0,
        favorites: Number(favorites) || 0,
        comments: Number(comments) || 0,
        shares: Number(shares) || 0,
        followers_gained: Number(followers) || 0,
        extra_metrics: {},
      });
      setCapturedAt(localNow());
      await Promise.all([loadPublicationAnalytics(selectedId), loadOverview()]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "数据保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="LEARN"
        title="数据分析"
        description="不是为了画更多图表，而是用结构化数据回答：什么内容值得继续做？"
      />
      {error ? <ErrorBanner message={error} /> : null}

      <div className="statsGrid">
        <StatCard label="总浏览" value={formatNumber(summary.views)} hint={`${summary.publications} 条有数据发布`} />
        <StatCard label="点赞" value={formatNumber(summary.likes)} />
        <StatCard label="收藏" value={formatNumber(summary.favorites)} />
        <StatCard label="涨粉" value={formatNumber(summary.followers_gained)} />
        <StatCard label="互动率" value={`${summary.engagement_rate}%`} hint="(赞+评+藏+分享) / 浏览" />
      </div>

      <Section title="哪些内容方向表现最好？" description="按 Content Pillar 聚合每个发布实例的最新数据快照。">
        {pillarAnalytics.length === 0 ? (
          <EmptyState>还没有可按内容支柱分析的数据。给 Content 设置 Pillar 并记录发布数据后，这里会开始形成方法论。</EmptyState>
        ) : (
          <div className="tableWrap">
            <table className="table">
              <thead><tr><th>Content Pillar</th><th>发布</th><th>平均浏览</th><th>互动率</th><th>收藏率</th><th>转粉率</th><th>总浏览</th></tr></thead>
              <tbody>
                {pillarAnalytics.map((item) => (
                  <tr key={item.pillar_id}>
                    <td><div className="tableTitle">{item.pillar_name}</div></td>
                    <td>{item.publications}</td>
                    <td>{formatNumber(Math.round(item.avg_views))}</td>
                    <td className="score">{item.engagement_rate}%</td>
                    <td className="score">{item.favorite_rate}%</td>
                    <td className="score high">{item.follower_conversion_rate}%</td>
                    <td>{formatNumber(item.views)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <div style={{ height: 16 }} />

      <Section title="用户兴趣是否在变化？" description="最近 30 天与前 30 天对比。上升/下降以平均浏览变化达到 ±20% 为信号，同时保留收藏率供判断内容价值。">
        {pillarTrends.length === 0 ? (
          <EmptyState>至少需要带 Content Pillar、实际发布时间和数据快照的发布记录，才能判断兴趣变化。</EmptyState>
        ) : (
          <div className="tableWrap">
            <table className="table">
              <thead><tr><th>Content Pillar</th><th>趋势</th><th>最近 / 前期发布</th><th>最近平均浏览</th><th>前期平均浏览</th><th>浏览变化</th><th>最近收藏率</th></tr></thead>
              <tbody>
                {pillarTrends.map((item) => {
                  const change = item.view_change_percent;
                  const changeLabel = change == null ? "—" : `${change > 0 ? "+" : ""}${change}%`;
                  const positive = item.signal === "rising" || item.signal === "new";
                  return (
                    <tr key={item.pillar_id}>
                      <td><div className="tableTitle">{item.pillar_name}</div></td>
                      <td className={`score ${positive ? "high" : ""}`}>{TREND_LABELS[item.signal]}</td>
                      <td>{item.recent_publications} / {item.previous_publications}</td>
                      <td>{formatNumber(Math.round(item.recent_avg_views))}</td>
                      <td>{formatNumber(Math.round(item.previous_avg_views))}</td>
                      <td className={`score ${change != null && change > 0 ? "high" : ""}`}>{changeLabel}</td>
                      <td>{item.recent_favorite_rate}%</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <div style={{ height: 16 }} />

      <Section title="哪个平台更适合我？" description="按平台聚合最新快照，比较平均浏览、互动、收藏和转粉效率。">
        {platformAnalytics.length === 0 ? (
          <EmptyState>还没有平台表现数据。为不同平台创建 Publication 并记录数据后，这里会自动比较。</EmptyState>
        ) : (
          <div className="tableWrap">
            <table className="table">
              <thead><tr><th>平台</th><th>发布</th><th>平均浏览</th><th>互动率</th><th>收藏率</th><th>转粉率</th><th>总浏览</th></tr></thead>
              <tbody>
                {platformAnalytics.map((item) => (
                  <tr key={item.platform_id}>
                    <td><div className="tableTitle">{item.platform_name}</div><div className="dataRowMeta">{item.platform_slug}</div></td>
                    <td>{item.publications}</td>
                    <td>{formatNumber(Math.round(item.avg_views))}</td>
                    <td className="score">{item.engagement_rate}%</td>
                    <td className="score">{item.favorite_rate}%</td>
                    <td className="score high">{item.follower_conversion_rate}%</td>
                    <td>{formatNumber(item.views)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Section>

      <div style={{ height: 16 }} />

      <div className="splitGrid">
        <form className="formCard" onSubmit={submit}>
          <div className="sectionHeading"><div><h2>记录数据快照</h2><p>同一发布实例可以在 24h、72h、7d、30d 多次记录。</p></div></div>
          {publications.length === 0 ? (
            <EmptyState>还没有发布实例。先到“发布管理”创建一条记录。</EmptyState>
          ) : (
            <div className="formGrid three">
              <div className="field full">
                <label htmlFor="metric-publication">发布实例</label>
                <select id="metric-publication" className="select" value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
                  {publications.map((item) => <option key={item.id} value={item.id}>{item.title || contentMap.get(item.content_id)?.title || "未命名发布"}</option>)}
                </select>
              </div>
              <div className="field">
                <label htmlFor="metric-time">采集时间</label>
                <input id="metric-time" className="input" type="datetime-local" value={capturedAt} onChange={(e) => setCapturedAt(e.target.value)} />
              </div>
              {[
                ["浏览", views, setViews], ["点赞", likes, setLikes], ["收藏", favorites, setFavorites],
                ["评论", comments, setComments], ["分享", shares, setShares], ["涨粉", followers, setFollowers],
              ].map(([label, value, setter]) => (
                <div className="field" key={label as string}>
                  <label>{label as string}</label>
                  <input className="input" min="0" type="number" value={value as string} onChange={(e) => (setter as (value: string) => void)(e.target.value)} />
                </div>
              ))}
              <div className="formActions"><button className="button" disabled={saving || !selectedId} type="submit">{saving ? "保存中…" : "保存快照"}</button></div>
            </div>
          )}
        </form>

        <Section title="当前快照" description={selectedPublication?.title || "选择一个发布实例查看数据"}>
          {!latest ? (
            <EmptyState>这条发布还没有数据快照。</EmptyState>
          ) : (
            <>
              <div className="metricGrid">
                <div className="metricBox"><span>浏览</span><strong>{formatNumber(latest.views)}</strong></div>
                <div className="metricBox"><span>点赞</span><strong>{formatNumber(latest.likes)}</strong></div>
                <div className="metricBox"><span>收藏</span><strong>{formatNumber(latest.favorites)}</strong></div>
                <div className="metricBox"><span>涨粉</span><strong>{formatNumber(latest.followers_gained)}</strong></div>
              </div>
              <p className="dataRowMeta" style={{ marginTop: 12 }}>最新采集：{formatDate(latest.captured_at)} · 已累计 {metrics.length} 个时间点</p>
            </>
          )}
        </Section>
      </div>

      <Section title="发布后关键时间窗口" description="里程碑使用发布后达到目标时间的第一条数据快照；没有对应快照时保持为空，不猜测数据。">
        {!selectedPublication?.published_at ? (
          <EmptyState>这条 Publication 还没有实际发布时间，因此暂时无法计算 24h / 72h / 7d / 30d。</EmptyState>
        ) : (
          <div className="metricGrid">
            {milestones.map((item) => (
              <div className="metricBox" key={item.label}>
                <span>{item.label} · 浏览</span>
                <strong>{item.views == null ? "—" : formatNumber(item.views)}</strong>
                <div className="dataRowMeta" style={{ marginTop: 7 }}>
                  收藏 {item.favorites == null ? "—" : formatNumber(item.favorites)} · 涨粉 {item.followers_gained == null ? "—" : formatNumber(item.followers_gained)}
                </div>
                <div className="dataRowMeta" style={{ marginTop: 3 }}>
                  {item.captured_at ? `采集 ${formatDate(item.captured_at)}` : `目标 ${formatDate(item.target_at)}`}
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>

      <div style={{ height: 16 }} />

      <Section title="历史快照" description="保留增长曲线所需要的时间序列，而不是覆盖上一组数字。">
        {metrics.length === 0 ? (
          <EmptyState>暂无历史记录。</EmptyState>
        ) : (
          <div className="tableWrap"><table className="table"><thead><tr><th>时间</th><th>浏览</th><th>点赞</th><th>收藏</th><th>评论</th><th>分享</th><th>涨粉</th></tr></thead><tbody>
            {metrics.map((item) => <tr key={item.id}><td>{formatDate(item.captured_at)}</td><td>{formatNumber(item.views)}</td><td>{formatNumber(item.likes)}</td><td>{formatNumber(item.favorites)}</td><td>{formatNumber(item.comments)}</td><td>{formatNumber(item.shares)}</td><td>{formatNumber(item.followers_gained)}</td></tr>)}
          </tbody></table></div>
        )}
      </Section>
    </>
  );
}
