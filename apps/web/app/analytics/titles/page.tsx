"use client";

import { useCallback, useEffect, useState } from "react";

import { EmptyState, ErrorBanner, PageHeader, Section, StatCard, formatNumber } from "@/components/ui";
import { api } from "@/lib/api";

type TitlePatternAnalyticsItem = {
  pattern: string;
  label: string;
  publications: number;
  views: number;
  likes: number;
  comments: number;
  favorites: number;
  shares: number;
  followers_gained: number;
  avg_views: number;
  engagement_rate: number;
  favorite_rate: number;
  follower_conversion_rate: number;
};

export default function TitleAnalyticsPage() {
  const [items, setItems] = useState<TitlePatternAnalyticsItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setItems(await api<TitlePatternAnalyticsItem[]>("/analytics/title-patterns"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "标题分析加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const bestByViews = items[0];
  const bestByFavorites = [...items].sort((a, b) => b.favorite_rate - a.favorite_rate)[0];
  const bestByFollowers = [...items].sort(
    (a, b) => b.follower_conversion_rate - a.follower_conversion_rate,
  )[0];

  return (
    <>
      <PageHeader
        eyebrow="TITLE INTELLIGENCE"
        title="标题模式分析"
        description="用真实发布数据比较疑问型、数字型、清单型、教程型和结果型标题，而不是凭感觉判断标题有效性。"
        action={<button className="button secondary" onClick={() => void load()}>刷新</button>}
      />
      {error ? <ErrorBanner message={error} /> : null}

      <div className="statsGrid" style={{ gridTemplateColumns: "repeat(3, minmax(0, 1fr))" }}>
        <StatCard
          label="平均浏览最佳"
          value={bestByViews?.label ?? "—"}
          hint={bestByViews ? `${formatNumber(Math.round(bestByViews.avg_views))} / 条` : "等待发布数据"}
        />
        <StatCard
          label="收藏率最佳"
          value={bestByFavorites?.label ?? "—"}
          hint={bestByFavorites ? `${bestByFavorites.favorite_rate}%` : "等待发布数据"}
        />
        <StatCard
          label="转粉率最佳"
          value={bestByFollowers?.label ?? "—"}
          hint={bestByFollowers ? `${bestByFollowers.follower_conversion_rate}%` : "等待发布数据"}
        />
      </div>

      <Section
        title="标题模式表现"
        description="一个标题可以同时命中多个模式，例如“为什么这 5 个技巧能提升收藏率？”同时属于疑问型、数字/清单型和结果型。"
      >
        {loading ? (
          <div className="loadingBlock">正在分析标题模式…</div>
        ) : items.length === 0 ? (
          <EmptyState>还没有带数据快照的 Publication。积累几条真实发布数据后，这里才有比较价值。</EmptyState>
        ) : (
          <div className="tableWrap">
            <table className="table">
              <thead>
                <tr>
                  <th>模式</th>
                  <th>样本数</th>
                  <th>平均浏览</th>
                  <th>互动率</th>
                  <th>收藏率</th>
                  <th>转粉率</th>
                  <th>总浏览</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.pattern}>
                    <td><div className="tableTitle">{item.label}</div><div className="dataRowMeta">{item.pattern}</div></td>
                    <td>{item.publications}</td>
                    <td className="score">{formatNumber(Math.round(item.avg_views))}</td>
                    <td>{item.engagement_rate}%</td>
                    <td>{item.favorite_rate}%</td>
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

      <Section title="如何使用这组数据" description="标题分析是决策辅助，不是“万能标题公式”。">
        <div className="twoColumns">
          <div>
            <div className="kicker">看目标指标</div>
            <p className="muted" style={{ lineHeight: 1.7, fontSize: 13 }}>
              想拉曝光时优先比较平均浏览；知识型内容更应该看收藏率；需要增长账号时再看转粉率。不要用单一播放量评价所有内容。
            </p>
          </div>
          <div>
            <div className="kicker">看样本量</div>
            <p className="muted" style={{ lineHeight: 1.7, fontSize: 13 }}>
              只有 1–2 条样本时不要形成强结论。随着 Creator Ops 持续积累 Publication 和 Metric Snapshot，这个分析才会逐渐变成你的个人标题方法论。
            </p>
          </div>
        </div>
      </Section>
    </>
  );
}
