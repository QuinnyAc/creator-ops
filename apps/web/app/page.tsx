"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import type { AnalyticsSummary, ContentItem, DashboardSummary, TopicRecommendation } from "@/lib/types";
import {
  Badge,
  EmptyState,
  ErrorBanner,
  LoadingBlock,
  PageHeader,
  Section,
  StatCard,
  formatNumber,
} from "@/components/ui";

const EMPTY_DASHBOARD: DashboardSummary = {
  inspirations_inbox: 0,
  topics_approved: 0,
  contents_in_progress: 0,
  publications_scheduled: 0,
  contents_to_review: 0,
};

const EMPTY_ANALYTICS: AnalyticsSummary = {
  publications: 0,
  views: 0,
  likes: 0,
  comments: 0,
  favorites: 0,
  shares: 0,
  followers_gained: 0,
  engagement_rate: 0,
};

export default function DashboardPage() {
  const [summary, setSummary] = useState(EMPTY_DASHBOARD);
  const [analytics, setAnalytics] = useState(EMPTY_ANALYTICS);
  const [recommendations, setRecommendations] = useState<TopicRecommendation[]>([]);
  const [contents, setContents] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [nextSummary, nextAnalytics, nextRecommendations, nextContents] = await Promise.all([
        api<DashboardSummary>("/dashboard/summary"),
        api<AnalyticsSummary>("/analytics/summary"),
        api<TopicRecommendation[]>("/recommendations/topics?limit=5"),
        api<ContentItem[]>("/contents"),
      ]);
      setSummary(nextSummary);
      setAnalytics(nextAnalytics);
      setRecommendations(nextRecommendations);
      setContents(nextContents);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Dashboard 加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const pipeline = useMemo(() => {
    const counts = new Map<string, number>();
    for (const content of contents) {
      counts.set(content.status, (counts.get(content.status) ?? 0) + 1);
    }
    return [...counts.entries()].sort((a, b) => b[1] - a[1]);
  }, [contents]);

  return (
    <>
      <PageHeader
        eyebrow="TODAY"
        title="创作控制台"
        description="先看到今天该做什么，再看到过去发生了什么。"
        action={<button className="button secondary" onClick={() => void load()}>刷新数据</button>}
      />
      {error ? <ErrorBanner message={error} /> : null}
      {loading ? (
        <LoadingBlock />
      ) : (
        <>
          <div className="statsGrid">
            <StatCard label="灵感 Inbox" value={summary.inspirations_inbox} hint="等待判断是否转为选题" />
            <StatCard label="制作中" value={summary.contents_in_progress} hint="Research → Ready" />
            <StatCard label="待发布" value={summary.publications_scheduled} hint="已经进入发布日程" />
            <StatCard label="待复盘" value={summary.contents_to_review} hint="把经验写回下一轮" />
            <StatCard label="总浏览" value={formatNumber(analytics.views)} hint={`互动率 ${analytics.engagement_rate}%`} />
          </div>

          <div className="dashboardGrid">
            <div className="stack">
              <Section
                title="下一条建议做什么？"
                description="人工选题优先级叠加 Content Pillar 历史表现和最近兴趣趋势；所有加减分都有可解释证据。"
                action={<Link className="link" href="/topics">查看选题库 →</Link>}
              >
                {recommendations.length === 0 ? (
                  <EmptyState>还没有可推荐的已评分选题。先为 Evaluating / Approved / Scheduled 选题完成评分。</EmptyState>
                ) : (
                  <div className="dataList">
                    {recommendations.map((item) => (
                      <div className="dataRow" key={item.topic_id} style={{ alignItems: "flex-start" }}>
                        <div style={{ minWidth: 0, flex: 1 }}>
                          <div className="dataRowTitle">{item.title}</div>
                          <div className="dataRowMeta">
                            {item.pillar_name ?? "未设置 Pillar"} · {item.status} · 人工优先级 {item.base_priority_score.toFixed(0)}
                            {item.evidence_adjustment === 0 ? "" : ` · 证据调整 ${item.evidence_adjustment > 0 ? "+" : ""}${item.evidence_adjustment.toFixed(0)}`}
                          </div>
                          <div className="dataRowMeta" style={{ marginTop: 5 }}>
                            {item.reasons[0] ?? "暂无额外证据"}
                          </div>
                        </div>
                        <div className="score high" title="Evidence-backed recommended score">{item.recommended_score.toFixed(0)}</div>
                      </div>
                    ))}
                  </div>
                )}
              </Section>

              <Section
                title="最近内容"
                description="正在推进的内容资产。"
                action={<Link className="link" href="/content">打开 Pipeline →</Link>}
              >
                {contents.length === 0 ? (
                  <EmptyState>还没有内容。把一个已确认的选题推进到生产环节。</EmptyState>
                ) : (
                  <div className="dataList">
                    {contents.slice(0, 6).map((content) => (
                      <div className="dataRow" key={content.id}>
                        <div>
                          <div className="dataRowTitle">{content.title}</div>
                          <div className="dataRowMeta">{content.content_type}</div>
                        </div>
                        <Badge value={content.status} />
                      </div>
                    ))}
                  </div>
                )}
              </Section>
            </div>

            <div className="stack">
              <Section title="内容 Pipeline" description="当前生产流中的工作量分布。">
                {pipeline.length === 0 ? (
                  <EmptyState>Pipeline 还是空的。</EmptyState>
                ) : (
                  <div className="dataList">
                    {pipeline.map(([status, count]) => (
                      <div className="dataRow" key={status}>
                        <Badge value={status} />
                        <strong>{count}</strong>
                      </div>
                    ))}
                  </div>
                )}
              </Section>

              <Section title="近期表现" description="使用每条发布实例最新一次数据快照计算。">
                <div className="metricGrid">
                  <div className="metricBox"><span>发布</span><strong>{analytics.publications}</strong></div>
                  <div className="metricBox"><span>点赞</span><strong>{formatNumber(analytics.likes)}</strong></div>
                  <div className="metricBox"><span>收藏</span><strong>{formatNumber(analytics.favorites)}</strong></div>
                  <div className="metricBox"><span>涨粉</span><strong>{formatNumber(analytics.followers_gained)}</strong></div>
                </div>
              </Section>
            </div>
          </div>
        </>
      )}
    </>
  );
}
