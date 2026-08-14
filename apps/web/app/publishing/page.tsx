"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { PlusIcon } from "@/components/icons";
import {
  Badge,
  EmptyState,
  ErrorBanner,
  PageHeader,
  Section,
  formatDate,
  formatNumber,
} from "@/components/ui";
import { api, patchJson, postJson } from "@/lib/api";
import type {
  ContentItem,
  MetricSnapshot,
  Platform,
  PlatformAccount,
  Publication,
} from "@/lib/types";

const PUBLICATION_STATUSES = ["draft", "scheduled", "published", "failed", "archived"];
const WEEKDAYS = ["一", "二", "三", "四", "五", "六", "日"];

function dateKey(date: Date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function publicationDate(item: Publication) {
  return item.scheduled_at || item.published_at;
}

function metricDisplay(snapshot: MetricSnapshot | undefined, field: "views" | "likes" | "comments" | "favorites") {
  if (!snapshot) return "—";
  if (field === "favorites" && snapshot.extra_metrics?.favorites_available === "false") return "—";
  return formatNumber(snapshot[field]);
}

export default function PublishingPage() {
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [accounts, setAccounts] = useState<PlatformAccount[]>([]);
  const [contents, setContents] = useState<ContentItem[]>([]);
  const [publications, setPublications] = useState<Publication[]>([]);
  const [latestMetrics, setLatestMetrics] = useState<Record<string, MetricSnapshot>>({});
  const [urlDrafts, setUrlDrafts] = useState<Record<string, string>>({});
  const [month, setMonth] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [syncingId, setSyncingId] = useState("");

  const [accountPlatformId, setAccountPlatformId] = useState("");
  const [accountName, setAccountName] = useState("");
  const [accountHandle, setAccountHandle] = useState("");

  const [contentId, setContentId] = useState("");
  const [accountId, setAccountId] = useState("");
  const [publicationTitle, setPublicationTitle] = useState("");
  const [publicationStatus, setPublicationStatus] = useState("draft");
  const [publicationUrl, setPublicationUrl] = useState("");
  const [scheduledAt, setScheduledAt] = useState("");

  const refreshLatestMetrics = useCallback(async () => {
    const snapshots = await api<MetricSnapshot[]>("/publication-metrics/latest");
    setLatestMetrics(Object.fromEntries(snapshots.map((item) => [item.publication_id, item])));
  }, []);

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
      setPublications(nextPublications);
      setLatestMetrics(Object.fromEntries(nextMetrics.map((item) => [item.publication_id, item])));
      setUrlDrafts((current) => {
        const next = { ...current };
        for (const publication of nextPublications) {
          if (!(publication.id in next)) next[publication.id] = publication.url ?? "";
        }
        return next;
      });
      setAccountPlatformId((current) => current || nextPlatforms[0]?.id || "");
      setAccountId((current) => current || nextAccounts[0]?.id || "");
      setContentId((current) => current || nextContents[0]?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "发布数据加载失败");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      void refreshLatestMetrics().catch(() => undefined);
    }, 20_000);
    return () => window.clearInterval(timer);
  }, [refreshLatestMetrics]);

  const platformMap = useMemo(() => new Map(platforms.map((item) => [item.id, item])), [platforms]);
  const accountMap = useMemo(() => new Map(accounts.map((item) => [item.id, item])), [accounts]);
  const contentMap = useMemo(() => new Map(contents.map((item) => [item.id, item])), [contents]);

  useEffect(() => {
    async function autoSyncYouTube() {
      const targets = publications.filter((item) => {
        if (!item.url || item.status !== "published") return false;
        const account = accountMap.get(item.platform_account_id);
        const platform = account ? platformMap.get(account.platform_id) : undefined;
        return platform?.slug === "youtube";
      });
      if (targets.length === 0) return;
      await Promise.all(
        targets.map((item) =>
          api<MetricSnapshot>(`/publications/${item.id}/sync-metrics`, { method: "POST" }).catch(() => null),
        ),
      );
      await refreshLatestMetrics().catch(() => undefined);
    }

    const initial = window.setTimeout(() => void autoSyncYouTube(), 5_000);
    const timer = window.setInterval(() => void autoSyncYouTube(), 60_000);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(timer);
    };
  }, [publications, accountMap, platformMap, refreshLatestMetrics]);

  const publicationsByDay = useMemo(() => {
    const map = new Map<string, Publication[]>();
    for (const item of publications) {
      const value = publicationDate(item);
      if (!value) continue;
      const key = dateKey(new Date(value));
      const list = map.get(key) ?? [];
      list.push(item);
      map.set(key, list);
    }
    return map;
  }, [publications]);

  const calendarCells = useMemo(() => {
    const first = new Date(month.getFullYear(), month.getMonth(), 1);
    const daysInMonth = new Date(month.getFullYear(), month.getMonth() + 1, 0).getDate();
    const mondayOffset = (first.getDay() + 6) % 7;
    const totalCells = Math.ceil((mondayOffset + daysInMonth) / 7) * 7;
    return Array.from({ length: totalCells }, (_, index) => {
      const dayNumber = index - mondayOffset + 1;
      return dayNumber >= 1 && dayNumber <= daysInMonth
        ? new Date(month.getFullYear(), month.getMonth(), dayNumber)
        : null;
    });
  }, [month]);

  async function addAccount(event: FormEvent) {
    event.preventDefault();
    if (!accountPlatformId || !accountName.trim()) return;
    setSaving(true);
    setError("");
    try {
      await postJson<PlatformAccount>("/platform-accounts", {
        platform_id: accountPlatformId,
        name: accountName.trim(),
        handle: accountHandle.trim() || null,
      });
      setAccountName("");
      setAccountHandle("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "账号添加失败");
    } finally {
      setSaving(false);
    }
  }

  async function addPublication(event: FormEvent) {
    event.preventDefault();
    if (!contentId || !accountId) return;
    setSaving(true);
    setError("");
    try {
      const content = contentMap.get(contentId);
      const created = await postJson<Publication>("/publications", {
        content_id: contentId,
        platform_account_id: accountId,
        title: publicationTitle.trim() || content?.title || null,
        status: publicationStatus,
        scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
        published_at: publicationStatus === "published" ? new Date().toISOString() : null,
        platform_tags: [],
        url: publicationUrl.trim() || null,
      });
      if (publicationStatus === "published" && publicationUrl.trim()) {
        await api<MetricSnapshot>(`/publications/${created.id}/sync-metrics`, { method: "POST" }).catch(() => null);
      }
      if (scheduledAt) {
        const nextDate = new Date(scheduledAt);
        setMonth(new Date(nextDate.getFullYear(), nextDate.getMonth(), 1));
      }
      setPublicationTitle("");
      setPublicationUrl("");
      setScheduledAt("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "发布记录创建失败");
    } finally {
      setSaving(false);
    }
  }

  async function updateStatus(item: Publication, status: string) {
    setError("");
    try {
      const payload: Record<string, string> = { status };
      if (status === "published" && !item.published_at) payload.published_at = new Date().toISOString();
      await patchJson<Publication>(`/publications/${item.id}`, payload);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "发布状态更新失败");
    }
  }

  async function syncMetrics(item: Publication, silent = false) {
    setSyncingId(item.id);
    if (!silent) setError("");
    try {
      const snapshot = await api<MetricSnapshot>(`/publications/${item.id}/sync-metrics`, { method: "POST" });
      setLatestMetrics((current) => ({ ...current, [item.id]: snapshot }));
    } catch (err) {
      if (!silent) setError(err instanceof Error ? err.message : "数据同步失败");
    } finally {
      setSyncingId("");
    }
  }

  async function saveUrl(item: Publication) {
    const nextUrl = (urlDrafts[item.id] ?? "").trim();
    setError("");
    try {
      const updated = await patchJson<Publication>(`/publications/${item.id}`, { url: nextUrl || null });
      setPublications((current) => current.map((entry) => (entry.id === item.id ? updated : entry)));
      if (updated.status === "published" && updated.url) await syncMetrics(updated, true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "作品链接保存失败");
    }
  }

  function shiftMonth(delta: number) {
    setMonth((current) => new Date(current.getFullYear(), current.getMonth() + delta, 1));
  }

  return (
    <>
      <PageHeader
        eyebrow="PUBLISH"
        title="发布管理"
        description="记录作品发布链接，并在同一处查看播放、点赞、评论、收藏等动态表现。"
      />
      {error ? <ErrorBanner message={error} /> : null}

      <div className="twoColumns">
        <form className="formCard" onSubmit={addAccount}>
          <div className="sectionHeading"><div><h2>平台账号</h2><p>同一平台可以管理多个创作者账号。</p></div></div>
          <div className="formGrid">
            <div className="field">
              <label htmlFor="account-platform">平台</label>
              <select id="account-platform" className="select" value={accountPlatformId} onChange={(e) => setAccountPlatformId(e.target.value)}>
                {platforms.map((platform) => <option key={platform.id} value={platform.id}>{platform.name}</option>)}
              </select>
            </div>
            <div className="field">
              <label htmlFor="account-name">账号名称</label>
              <input id="account-name" className="input" value={accountName} onChange={(e) => setAccountName(e.target.value)} placeholder="例如：Quinny" />
            </div>
            <div className="field full">
              <label htmlFor="account-handle">Handle / UID</label>
              <input id="account-handle" className="input" value={accountHandle} onChange={(e) => setAccountHandle(e.target.value)} placeholder="可选" />
            </div>
            <div className="formActions"><button className="button" disabled={saving || !accountName.trim()} type="submit"><PlusIcon width={16} height={16} />添加账号</button></div>
          </div>
        </form>

        <form className="formCard" onSubmit={addPublication}>
          <div className="sectionHeading"><div><h2>创建发布实例</h2><p>作品发布后可直接粘贴平台链接。</p></div></div>
          <div className="formGrid">
            <div className="field">
              <label htmlFor="publish-content">内容</label>
              <select id="publish-content" className="select" value={contentId} onChange={(e) => setContentId(e.target.value)}>
                <option value="">选择内容</option>
                {contents.map((content) => <option key={content.id} value={content.id}>{content.title}</option>)}
              </select>
            </div>
            <div className="field">
              <label htmlFor="publish-account">账号</label>
              <select id="publish-account" className="select" value={accountId} onChange={(e) => setAccountId(e.target.value)}>
                <option value="">选择账号</option>
                {accounts.map((account) => <option key={account.id} value={account.id}>{platformMap.get(account.platform_id)?.name} · {account.name}</option>)}
              </select>
            </div>
            <div className="field full">
              <label htmlFor="publish-title">平台标题</label>
              <input id="publish-title" className="input" value={publicationTitle} onChange={(e) => setPublicationTitle(e.target.value)} placeholder="留空则使用内容标题" />
            </div>
            <div className="field full">
              <label htmlFor="publish-url">已发布作品链接</label>
              <input id="publish-url" className="input" type="url" value={publicationUrl} onChange={(e) => setPublicationUrl(e.target.value)} placeholder="https://...  发布后粘贴即可" />
            </div>
            <div className="field">
              <label htmlFor="publish-status">状态</label>
              <select id="publish-status" className="select" value={publicationStatus} onChange={(e) => setPublicationStatus(e.target.value)}>
                {PUBLICATION_STATUSES.slice(0, 3).map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </div>
            <div className="field">
              <label htmlFor="publish-time">计划发布时间</label>
              <input id="publish-time" className="input" type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} />
            </div>
            <div className="formActions"><button className="button" disabled={saving || !contentId || !accountId} type="submit">加入发布计划</button></div>
          </div>
        </form>
      </div>

      <Section
        title="发布日历"
        description="按月查看内容密度、平台节奏和空档日期。"
        action={
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <button className="button small secondary" type="button" onClick={() => shiftMonth(-1)}>←</button>
            <strong style={{ minWidth: 104, textAlign: "center", fontSize: 12 }}>{month.getFullYear()} / {month.getMonth() + 1}</strong>
            <button className="button small secondary" type="button" onClick={() => shiftMonth(1)}>→</button>
          </div>
        }
      >
        <div style={{ overflowX: "auto" }}>
          <div style={{ minWidth: 850 }}>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(7, minmax(0, 1fr))", gap: 6, marginBottom: 6 }}>
              {WEEKDAYS.map((weekday) => <div key={weekday} style={{ padding: "8px 9px", color: "var(--muted)", fontSize: 10, fontWeight: 800, textAlign: "center" }}>周{weekday}</div>)}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(7, minmax(0, 1fr))", gap: 6 }}>
              {calendarCells.map((date, index) => {
                if (!date) return <div key={`blank-${index}`} style={{ minHeight: 126, background: "#fafafa", borderRadius: 10 }} />;
                const key = dateKey(date);
                const items = publicationsByDay.get(key) ?? [];
                const isToday = key === dateKey(new Date());
                return (
                  <div key={key} style={{ minHeight: 126, border: `1px solid ${isToday ? "#9b96ff" : "var(--line)"}`, borderRadius: 10, padding: 8, background: "#fff", boxShadow: isToday ? "0 0 0 2px rgba(91,85,247,.08)" : "none" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 7 }}>
                      <strong style={{ fontSize: 11 }}>{date.getDate()}</strong>
                      {items.length > 0 ? <span className="kanbanCount">{items.length}</span> : null}
                    </div>
                    <div style={{ display: "grid", gap: 5 }}>
                      {items.slice(0, 3).map((item) => {
                        const account = accountMap.get(item.platform_account_id);
                        const platform = account ? platformMap.get(account.platform_id) : undefined;
                        return (
                          <div key={item.id} style={{ borderRadius: 7, padding: "6px 7px", background: item.status === "published" ? "var(--green-soft)" : "var(--accent-soft)" }}>
                            <div style={{ fontSize: 9, fontWeight: 800, color: item.status === "published" ? "var(--green)" : "#4b43d7" }}>{platform?.name ?? "平台"}</div>
                            <div style={{ fontSize: 10, fontWeight: 650, lineHeight: 1.35, marginTop: 2, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{item.title || contentMap.get(item.content_id)?.title || "未命名发布"}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </Section>

      <div style={{ height: 16 }} />

      <Section title={`发布记录 · ${publications.length}`} description="作品链接、发布状态和最新数据都集中在这里；最新快照每 20 秒刷新。">
        {publications.length === 0 ? (
          <EmptyState>{accounts.length === 0 ? "先添加一个平台账号，再为内容创建发布实例。" : "还没有发布计划。"}</EmptyState>
        ) : (
          <div style={{ display: "grid", gap: 12 }}>
            {publications.map((item) => {
              const account = accountMap.get(item.platform_account_id);
              const platform = account ? platformMap.get(account.platform_id) : undefined;
              const content = contentMap.get(item.content_id);
              const snapshot = latestMetrics[item.id];
              const draftUrl = urlDrafts[item.id] ?? item.url ?? "";
              return (
                <div className="formCard" key={item.id} style={{ marginBottom: 0 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "flex-start", flexWrap: "wrap" }}>
                    <div style={{ minWidth: 240, flex: 1 }}>
                      <div className="dataRowTitle">{item.title || content?.title || "未命名发布"}</div>
                      <div className="dataRowMeta" style={{ marginTop: 4 }}>{platform?.name ?? "平台"} · {account?.name ?? "账号"} · {formatDate(item.scheduled_at || item.published_at)}</div>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <Badge value={item.status} />
                      <select className="inlineSelect" value={item.status} onChange={(e) => void updateStatus(item, e.target.value)}>
                        {PUBLICATION_STATUSES.map((value) => <option key={value} value={value}>{value}</option>)}
                      </select>
                    </div>
                  </div>

                  <div style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 8, marginTop: 14 }}>
                    <div className="metricBox"><span>播放</span><strong>{metricDisplay(snapshot, "views")}</strong></div>
                    <div className="metricBox"><span>点赞</span><strong>{metricDisplay(snapshot, "likes")}</strong></div>
                    <div className="metricBox"><span>评论</span><strong>{metricDisplay(snapshot, "comments")}</strong></div>
                    <div className="metricBox"><span>收藏</span><strong>{metricDisplay(snapshot, "favorites")}</strong></div>
                  </div>

                  <div style={{ display: "flex", gap: 8, marginTop: 12, flexWrap: "wrap", alignItems: "center" }}>
                    <input
                      className="input"
                      type="url"
                      value={draftUrl}
                      onChange={(e) => setUrlDrafts((current) => ({ ...current, [item.id]: e.target.value }))}
                      placeholder="粘贴已发布作品链接"
                      style={{ flex: "1 1 360px" }}
                    />
                    <button className="button small secondary" type="button" onClick={() => void saveUrl(item)}>保存链接</button>
                    {item.url ? <a className="button small ghost" href={item.url} target="_blank" rel="noreferrer">打开作品 ↗</a> : null}
                    {item.url ? <button className="button small" type="button" disabled={syncingId === item.id} onClick={() => void syncMetrics(item)}>{syncingId === item.id ? "同步中…" : "立即同步数据"}</button> : null}
                  </div>

                  <div className="dataRowMeta" style={{ marginTop: 9 }}>
                    {snapshot ? `最近数据：${formatDate(snapshot.captured_at)}` : "尚无数据快照"}
                    {platform?.slug === "youtube" ? " · 页面打开期间每 60 秒尝试通过 YouTube 官方 API 更新" : ""}
                    {platform?.slug === "bilibili" ? " · B站自动数据需要开放平台授权" : ""}
                    {platform?.slug === "xiaohongshu" ? " · 小红书当前保留链接与快照展示，官方自动数据接口待接入" : ""}
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
