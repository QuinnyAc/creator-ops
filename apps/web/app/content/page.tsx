"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { PlusIcon } from "@/components/icons";
import { EmptyState, ErrorBanner, PageHeader } from "@/components/ui";
import { api, patchJson, postJson } from "@/lib/api";
import type { ContentItem, ContentPillar, Topic } from "@/lib/types";

const COLUMNS = [
  "research",
  "outline",
  "script",
  "shooting",
  "editing",
  "ready",
  "published",
  "review",
] as const;

export default function ContentPipelinePage() {
  const [contents, setContents] = useState<ContentItem[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [pillars, setPillars] = useState<ContentPillar[]>([]);
  const [title, setTitle] = useState("");
  const [topicId, setTopicId] = useState("");
  const [pillarId, setPillarId] = useState("");
  const [contentType, setContentType] = useState("video");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setError("");
    try {
      const [nextContents, nextTopics, nextPillars] = await Promise.all([
        api<ContentItem[]>("/contents"),
        api<Topic[]>("/topics"),
        api<ContentPillar[]>("/content-pillars"),
      ]);
      setContents(nextContents);
      setTopics(nextTopics);
      setPillars(nextPillars);
    } catch (err) {
      setError(err instanceof Error ? err.message : "内容 Pipeline 加载失败");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const topicMap = useMemo(() => new Map(topics.map((topic) => [topic.id, topic])), [topics]);
  const pillarMap = useMemo(() => new Map(pillars.map((pillar) => [pillar.id, pillar])), [pillars]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    setError("");
    try {
      const topic = topicId ? topicMap.get(topicId) : undefined;
      await postJson<ContentItem>("/contents", {
        title: title.trim(),
        topic_id: topicId || null,
        pillar_id: pillarId || topic?.pillar_id || null,
        content_type: contentType,
        status: "research",
      });
      if (topicId) {
        await patchJson<Topic>(`/topics/${topicId}`, { status: "in_production" });
      }
      setTitle("");
      setTopicId("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建内容失败");
    } finally {
      setSaving(false);
    }
  }

  async function move(item: ContentItem, status: string) {
    setError("");
    try {
      await patchJson<ContentItem>(`/contents/${item.id}`, { status });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "内容状态更新失败");
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="EXECUTE"
        title="内容 Pipeline"
        description="把每一条内容的生产状态可视化，避免脚本、拍摄、剪辑和待发布混在一张表里。"
      />
      {error ? <ErrorBanner message={error} /> : null}

      <form className="formCard" onSubmit={submit}>
        <div className="formGrid three">
          <div className="field">
            <label htmlFor="content-title">内容标题</label>
            <input id="content-title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="准备制作的内容" />
          </div>
          <div className="field">
            <label htmlFor="content-topic">关联选题</label>
            <select id="content-topic" className="select" value={topicId} onChange={(e) => setTopicId(e.target.value)}>
              <option value="">不关联</option>
              {topics.filter((topic) => !["rejected", "archived", "completed"].includes(topic.status)).map((topic) => (
                <option key={topic.id} value={topic.id}>{topic.title}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="content-pillar">内容支柱</label>
            <select id="content-pillar" className="select" value={pillarId} onChange={(e) => setPillarId(e.target.value)}>
              <option value="">跟随选题 / 未分类</option>
              {pillars.map((pillar) => <option key={pillar.id} value={pillar.id}>{pillar.name}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="content-type">内容类型</label>
            <select id="content-type" className="select" value={contentType} onChange={(e) => setContentType(e.target.value)}>
              <option value="video">视频</option>
              <option value="article">图文 / 文章</option>
              <option value="short_video">短视频</option>
              <option value="newsletter">Newsletter</option>
            </select>
          </div>
          <div className="formActions">
            <button className="button" disabled={saving || !title.trim()} type="submit">
              <PlusIcon width={16} height={16} /> {saving ? "创建中…" : "进入生产"}
            </button>
          </div>
        </div>
      </form>

      {contents.length === 0 ? (
        <EmptyState>还没有生产中的内容。选一个值得做的题，把它推进到 Research。</EmptyState>
      ) : (
        <div className="kanban">
          {COLUMNS.map((column) => {
            const items = contents.filter((item) => item.status === column);
            return (
              <div className="kanbanColumn" key={column}>
                <div className="kanbanHeader">
                  <span>{column.replaceAll("_", " ")}</span>
                  <span className="kanbanCount">{items.length}</span>
                </div>
                <div className="kanbanCards">
                  {items.map((item) => (
                    <article className="kanbanCard" key={item.id}>
                      <h3>{item.title}</h3>
                      <p>
                        {item.topic_id ? topicMap.get(item.topic_id)?.title ?? "关联选题" : "独立内容"}
                        {item.pillar_id ? ` · ${pillarMap.get(item.pillar_id)?.name ?? ""}` : ""}
                      </p>
                      <div className="cardActions">
                        <select className="inlineSelect" value={item.status} onChange={(e) => void move(item, e.target.value)}>
                          {COLUMNS.map((status) => <option key={status} value={status}>{status}</option>)}
                        </select>
                        <Link className="link" href={`/content/${item.id}`}>打开 →</Link>
                      </div>
                    </article>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}
