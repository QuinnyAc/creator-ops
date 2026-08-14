"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { PlusIcon } from "@/components/icons";
import { Badge, EmptyState, ErrorBanner, PageHeader, Section, formatDate } from "@/components/ui";
import { api, patchJson, postJson } from "@/lib/api";
import type { ContentItem, Platform, PlatformAccount, Publication } from "@/lib/types";

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

export default function PublishingPage() {
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [accounts, setAccounts] = useState<PlatformAccount[]>([]);
  const [contents, setContents] = useState<ContentItem[]>([]);
  const [publications, setPublications] = useState<Publication[]>([]);
  const [month, setMonth] = useState(() => {
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth(), 1);
  });
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const [accountPlatformId, setAccountPlatformId] = useState("");
  const [accountName, setAccountName] = useState("");
  const [accountHandle, setAccountHandle] = useState("");

  const [contentId, setContentId] = useState("");
  const [accountId, setAccountId] = useState("");
  const [publicationTitle, setPublicationTitle] = useState("");
  const [publicationStatus, setPublicationStatus] = useState("draft");
  const [scheduledAt, setScheduledAt] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const [nextPlatforms, nextAccounts, nextContents, nextPublications] = await Promise.all([
        api<Platform[]>("/platforms"),
        api<PlatformAccount[]>("/platform-accounts"),
        api<ContentItem[]>("/contents"),
        api<Publication[]>("/publications"),
      ]);
      setPlatforms(nextPlatforms);
      setAccounts(nextAccounts);
      setContents(nextContents);
      setPublications(nextPublications);
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

  const platformMap = useMemo(() => new Map(platforms.map((item) => [item.id, item])), [platforms]);
  const accountMap = useMemo(() => new Map(accounts.map((item) => [item.id, item])), [accounts]);
  const contentMap = useMemo(() => new Map(contents.map((item) => [item.id, item])), [contents]);

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
      await postJson<Publication>("/publications", {
        content_id: contentId,
        platform_account_id: accountId,
        title: publicationTitle.trim() || content?.title || null,
        status: publicationStatus,
        scheduled_at: scheduledAt ? new Date(scheduledAt).toISOString() : null,
        platform_tags: [],
      });
      if (scheduledAt) {
        const nextDate = new Date(scheduledAt);
        setMonth(new Date(nextDate.getFullYear(), nextDate.getMonth(), 1));
      }
      setPublicationTitle("");
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
      if (status === "published" && !item.published_at) {
        payload.published_at = new Date().toISOString();
      }
      await patchJson<Publication>(`/publications/${item.id}`, payload);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "发布状态更新失败");
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
        description="管理什么时候发、发到哪里、哪个账号、是否已发，并用月历检查内容节奏。"
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
              <input id="account-name" className="input" value={accountName} onChange={(e) => setAccountName(e.target.value)} placeholder="例如：AI 实验室" />
            </div>
            <div className="field full">
              <label htmlFor="account-handle">Handle / UID</label>
              <input id="account-handle" className="input" value={accountHandle} onChange={(e) => setAccountHandle(e.target.value)} placeholder="可选" />
            </div>
            <div className="formActions"><button className="button" disabled={saving || !accountName.trim()} type="submit"><PlusIcon width={16} height={16} />添加账号</button></div>
          </div>
        </form>

        <form className="formCard" onSubmit={addPublication}>
          <div className="sectionHeading"><div><h2>创建发布实例</h2><p>一份 Content 可以拥有多个平台 Publication。</p></div></div>
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
              {WEEKDAYS.map((weekday) => (
                <div key={weekday} style={{ padding: "8px 9px", color: "var(--muted)", fontSize: 10, fontWeight: 800, textAlign: "center" }}>周{weekday}</div>
              ))}
            </div>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(7, minmax(0, 1fr))", gap: 6 }}>
              {calendarCells.map((date, index) => {
                if (!date) {
                  return <div key={`blank-${index}`} style={{ minHeight: 126, background: "#fafafa", borderRadius: 10 }} />;
                }
                const key = dateKey(date);
                const items = publicationsByDay.get(key) ?? [];
                const isToday = key === dateKey(new Date());
                return (
                  <div
                    key={key}
                    style={{
                      minHeight: 126,
                      border: `1px solid ${isToday ? "#9b96ff" : "var(--line)"}`,
                      borderRadius: 10,
                      padding: 8,
                      background: "#fff",
                      boxShadow: isToday ? "0 0 0 2px rgba(91,85,247,.08)" : "none",
                    }}
                  >
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
                      {items.length > 3 ? <div className="dataRowMeta">还有 {items.length - 3} 条</div> : null}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </Section>

      <div style={{ height: 16 }} />

      <Section title={`发布记录 · ${publications.length}`} description="日历负责节奏，列表负责状态和精确时间。">
        {publications.length === 0 ? (
          <EmptyState>{accounts.length === 0 ? "先添加一个平台账号，再为内容创建发布实例。" : "还没有发布计划。"}</EmptyState>
        ) : (
          <div className="calendarList">
            {publications.map((item) => {
              const account = accountMap.get(item.platform_account_id);
              const platform = account ? platformMap.get(account.platform_id) : undefined;
              const content = contentMap.get(item.content_id);
              return (
                <div className="calendarItem" key={item.id}>
                  <div className="calendarDate">{formatDate(item.scheduled_at || item.published_at)}</div>
                  <div>
                    <div className="dataRowTitle">{item.title || content?.title || "未命名发布"}</div>
                    <div className="dataRowMeta">{platform?.name ?? "平台"} · {account?.name ?? "账号"} · 核心内容：{content?.title ?? "—"}</div>
                  </div>
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <Badge value={item.status} />
                    <select className="inlineSelect" value={item.status} onChange={(e) => void updateStatus(item, e.target.value)}>
                      {PUBLICATION_STATUSES.map((value) => <option key={value} value={value}>{value}</option>)}
                    </select>
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
