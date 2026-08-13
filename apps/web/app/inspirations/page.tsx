"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { PlusIcon } from "@/components/icons";
import { Badge, EmptyState, ErrorBanner, PageHeader, Section, formatDate } from "@/components/ui";
import { api, patchJson, postJson } from "@/lib/api";
import type { Inspiration, Topic } from "@/lib/types";

export default function InspirationsPage() {
  const [items, setItems] = useState<Inspiration[]>([]);
  const [title, setTitle] = useState("");
  const [note, setNote] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setItems(await api<Inspiration[]>("/inspirations"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "灵感加载失败");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    setError("");
    try {
      await postJson<Inspiration>("/inspirations", {
        title: title.trim(),
        note: note.trim() || null,
        source_url: sourceUrl.trim() || null,
        source: sourceUrl.trim() ? "web" : null,
      });
      setTitle("");
      setNote("");
      setSourceUrl("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  async function convert(item: Inspiration) {
    setError("");
    try {
      await postJson<Topic>(`/inspirations/${item.id}/convert`, {});
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "转为选题失败");
    }
  }

  async function archive(item: Inspiration) {
    setError("");
    try {
      await patchJson<Inspiration>(`/inspirations/${item.id}`, { status: "archived" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "归档失败");
    }
  }

  const inbox = items.filter((item) => item.status === "inbox");
  const processed = items.filter((item) => item.status !== "inbox");

  return (
    <>
      <PageHeader
        eyebrow="CAPTURE"
        title="灵感 Inbox"
        description="收集时保持低摩擦；真正需要判断价值时，再把它转换成结构化选题。"
      />
      {error ? <ErrorBanner message={error} /> : null}

      <form className="formCard" onSubmit={submit}>
        <div className="formGrid">
          <div className="field full">
            <label htmlFor="idea-title">一句话灵感</label>
            <input
              id="idea-title"
              className="input"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="例如：为什么知识型账号更应该关注收藏率而不是点赞？"
            />
          </div>
          <div className="field">
            <label htmlFor="idea-note">补充说明</label>
            <textarea id="idea-note" className="textarea" value={note} onChange={(event) => setNote(event.target.value)} />
          </div>
          <div className="field">
            <label htmlFor="idea-url">来源链接</label>
            <textarea id="idea-url" className="textarea" value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} placeholder="可选" />
          </div>
          <div className="formActions">
            <button className="button" disabled={saving || !title.trim()} type="submit">
              <PlusIcon width={16} height={16} /> {saving ? "保存中…" : "收进 Inbox"}
            </button>
          </div>
        </div>
      </form>

      <div className="splitGrid">
        <Section title={`待处理 · ${inbox.length}`} description="这里应该保持短小，只存还没有做决策的想法。">
          {inbox.length === 0 ? (
            <EmptyState>Inbox 已清空。新的想法随手记进来即可。</EmptyState>
          ) : (
            <div className="dataList">
              {inbox.map((item) => (
                <div className="dataRow" key={item.id}>
                  <div>
                    <div className="dataRowTitle">{item.title}</div>
                    <div className="dataRowMeta">{item.note || "无补充"} · {formatDate(item.created_at)}</div>
                  </div>
                  <div style={{ display: "flex", gap: 6 }}>
                    <button className="button small" onClick={() => void convert(item)}>转为选题</button>
                    <button className="button small secondary" onClick={() => void archive(item)}>归档</button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Section>

        <Section title="已处理" description="已经转换或归档的灵感记录。">
          {processed.length === 0 ? (
            <EmptyState>暂无已处理记录。</EmptyState>
          ) : (
            <div className="dataList">
              {processed.slice(0, 10).map((item) => (
                <div className="dataRow" key={item.id}>
                  <div>
                    <div className="dataRowTitle">{item.title}</div>
                    <div className="dataRowMeta">{formatDate(item.updated_at)}</div>
                  </div>
                  <Badge value={item.status} />
                </div>
              ))}
            </div>
          )}
        </Section>
      </div>
    </>
  );
}
