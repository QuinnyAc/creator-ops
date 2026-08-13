"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { api } from "@/lib/api";
import type { AnalyticsSummary, ContentItem, DashboardSummary, Topic } from "@/lib/types";
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
  const [topics, setTopics] = useState<Topic[]>([]);
  const [contents, setContents] = useState<ContentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [nextSummary, nextAnalytics, nextTopics, nextContents] = await Promise.all([
        api<DashboardSummary>("/dashboard/summary"),
        api<AnalyticsSummary>("/analytics/summary"),
        api<Topic[]>("/topics"),
        api<ContentItem[]>("/contents"),
      ]);
      setSummary(nextSummary);
      setAnalytics(nextAnalytics);
      setTopics(nextTopics);
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

  const topTopics = useMemo(
    () =>
      [...topics]
        .filter((topic) => topic.priority_score != null)
        .sort((a, b) => Number(b.priority_score) - Number(a.priority_score))
        .slice(0, 5),
    [topics],
  );

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
                title="高优先级选题"
                description="根据机会价值与制作成本计算下一步应该做什么。"
                action={<Link className="link" href="/topics">查看选题库 →</Link>}
              >
                {topTopics.length === 0 ? (
                  <EmptyState>还没有完成选题评分。先创建一个选题并给六个维度打分。</EmptyState>
                ) : (
                  <div className="dataList">
                    {topTopics.map((topic) => (
                      <div className="dataRow" key={topic.id}>
                        <div>
                          <div className="dataRowTitle">{topic.title}</div>
                          <div className="dataRowMeta">{topic.goal ?? "未设置目标"} · {topic.status}</div>
                        </div>
                        <div className="score high">{Number(topic.priority_score).toFixed(0)}</div>
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
