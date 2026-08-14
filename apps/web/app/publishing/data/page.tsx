"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";

import { EmptyState, ErrorBanner, LoadingBlock, PageHeader, Section, formatDate, formatNumber } from "@/components/ui";
import { api } from "@/lib/api";
import type { ContentItem, MetricSnapshot, Platform, PlatformAccount, Publication } from "@/lib/types";

export default function SingleVideoDataPage() {
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [accounts, setAccounts] = useState<PlatformAccount[]>([]);
  const [contents, setContents] = useState<ContentItem[]>([]);
  const [publications, setPublications] = useState<Publication[]>([]);
  const [metrics, setMetrics] = useState<Record<string, MetricSnapshot>>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const [nextPlatforms, nextAccounts, nextContents, nextPublications, nextMetrics] = await Promise.all([
        api<Platform[]>("/platforms"),
        api<PlatformAccount[]>("/platform-accounts"),
        api<ContentItem[]>("/contents"),
        api<Publication[]>("/publications"),
        api<MetricSnapshot[]>("/publication-metrics/latest"),
      ]);
      setPlatforms(nextPlatforms);
      setAccounts(nextAccounts);
      setContents(nextContents);
      setPublications(nextPublications.filter((item) => item.status === "published" || Boolean(item.url)));
      setMetrics(Object.fromEntries(nextMetrics.map((item) => [item.publication_id, item])));
    } catch (err) {
      setError(err instanceof Error ? err.message : "单视频数据加载失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => void load(), 20_000);
    return () => window.clearInterval(timer);
  }, [load]);

  const platformMap = useMemo(() => new Map(platforms.map((item) => [item.id, item])), [platforms]);
  const accountMap = useMemo(() => new Map(accounts.map((item) => [item.id, item])), [accounts]);
  const contentMap = useMemo(() => new Map(contents.map((item) => [item.id, item])), [contents]);

  if (loading) return <LoadingBlock />;

  return (
    <>
      <PageHeader
        eyebrow="VIDEO DATA"
        title="单视频数据"
        description="集中查看每一条已发布作品的最新表现，点击作品进入完整数据详情。"
        action={<Link className="button small secondary" href="/publishing">返回发布管理</Link>}
      />
      {error ? <ErrorBanner message={error} /> : null}

      <Section title={`已发布作品 · ${publications.length}`} description="最新数据每 20 秒刷新。">
        {publications.length === 0 ? (
          <EmptyState>还没有已发布作品。先在“发布管理”创建发布记录并填写作品链接。</EmptyState>
        ) : (
          <div style={{ display: "grid", gap: 12 }}>
            {publications.map((item) => {
              const account = accountMap.get(item.platform_account_id);
              const platform = account ? platformMap.get(account.platform_id) : undefined;
              const content = contentMap.get(item.content_id);
              const snapshot = metrics[item.id];
              return (
                <div className="formCard" key={item.id} style={{ marginBottom: 0 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16, flexWrap: "wrap" }}>
                    <div style={{ minWidth: 240, flex: 1 }}>
                      <div className="dataRowTitle">{item.title || content?.title || "未命名作品"}</div>
                      <div className="dataRowMeta" style={{ marginTop: 4 }}>
                        {platform?.name ?? "平台"} · {account?.name ?? "账号"} · {formatDate(item.published_at || item.scheduled_at)}
                      </div>
                    </div>
                    <Link className="button small" href={`/publishing/${item.id}`}>查看数据详情 →</Link>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 8, marginTop: 14 }}>
                    <div className="metricBox"><span>播放</span><strong>{snapshot ? formatNumber(snapshot.views) : "—"}</strong></div>
                    <div className="metricBox"><span>点赞</span><strong>{snapshot ? formatNumber(snapshot.likes) : "—"}</strong></div>
                    <div className="metricBox"><span>评论</span><strong>{snapshot ? formatNumber(snapshot.comments) : "—"}</strong></div>
                    <div className="metricBox"><span>收藏</span><strong>{snapshot ? formatNumber(snapshot.favorites) : "—"}</strong></div>
                  </div>

                  <div className="dataRowMeta" style={{ marginTop: 9 }}>
                    {snapshot ? `最近记录：${formatDate(snapshot.captured_at)}` : "尚未记录数据"}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </Section>
    </>
  );
}
