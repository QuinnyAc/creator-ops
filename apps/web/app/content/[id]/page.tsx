"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";

import { ErrorBanner, LoadingBlock, PageHeader, Section } from "@/components/ui";
import { api, patchJson } from "@/lib/api";
import type { ContentItem } from "@/lib/types";

const STATUSES = ["research", "outline", "script", "shooting", "editing", "ready", "published", "review"];

type Draft = {
  title: string;
  status: string;
  research_notes: string;
  outline: string;
  script: string;
  copywriting: string;
  cta: string;
  planned_publish_at: string;
};

function toLocalInput(value: string | null) {
  if (!value) return "";
  const date = new Date(value);
  const offset = date.getTimezoneOffset();
  return new Date(date.getTime() - offset * 60_000).toISOString().slice(0, 16);
}

export default function ContentWorkspacePage() {
  const params = useParams<{ id: string }>();
  const contentId = params.id;
  const [content, setContent] = useState<ContentItem | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const item = await api<ContentItem>(`/contents/${contentId}`);
      setContent(item);
      setDraft({
        title: item.title,
        status: item.status,
        research_notes: item.research_notes ?? "",
        outline: item.outline ?? "",
        script: item.script ?? "",
        copywriting: item.copywriting ?? "",
        cta: item.cta ?? "",
        planned_publish_at: toLocalInput(item.planned_publish_at),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "内容加载失败");
    } finally {
      setLoading(false);
    }
  }, [contentId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function save(event: FormEvent) {
    event.preventDefault();
    if (!draft) return;
    setSaving(true);
    setSaved(false);
    setError("");
    try {
      const updated = await patchJson<ContentItem>(`/contents/${contentId}`, {
        title: draft.title.trim(),
        status: draft.status,
        research_notes: draft.research_notes || null,
        outline: draft.outline || null,
        script: draft.script || null,
        copywriting: draft.copywriting || null,
        cta: draft.cta || null,
        planned_publish_at: draft.planned_publish_at ? new Date(draft.planned_publish_at).toISOString() : null,
      });
      setContent(updated);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingBlock />;

  return (
    <>
      <PageHeader
        eyebrow="CONTENT WORKSPACE"
        title={content?.title ?? "内容工作区"}
        description="研究、大纲、脚本、文案和 CTA 都属于同一个内容资产。"
        action={<Link className="button secondary" href="/content">← 返回 Pipeline</Link>}
      />
      {error ? <ErrorBanner message={error} /> : null}
      {!draft ? null : (
        <form className="stack" onSubmit={save}>
          <Section title="Overview" description="控制内容生命周期和计划发布时间。">
            <div className="formGrid three">
              <div className="field">
                <label htmlFor="workspace-title">标题</label>
                <input id="workspace-title" className="input" value={draft.title} onChange={(e) => setDraft({ ...draft, title: e.target.value })} />
              </div>
              <div className="field">
                <label htmlFor="workspace-status">状态</label>
                <select id="workspace-status" className="select" value={draft.status} onChange={(e) => setDraft({ ...draft, status: e.target.value })}>
                  {STATUSES.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </div>
              <div className="field">
                <label htmlFor="workspace-date">计划发布时间</label>
                <input id="workspace-date" className="input" type="datetime-local" value={draft.planned_publish_at} onChange={(e) => setDraft({ ...draft, planned_publish_at: e.target.value })} />
              </div>
            </div>
          </Section>

          <div className="twoColumns">
            <Section title="Research" description="事实、素材、用户问题、案例与参考资料。">
              <textarea className="textarea" style={{ minHeight: 260 }} value={draft.research_notes} onChange={(e) => setDraft({ ...draft, research_notes: e.target.value })} placeholder="研究笔记…" />
            </Section>
            <Section title="Outline" description="先搭内容结构，再进入完整脚本。">
              <textarea className="textarea" style={{ minHeight: 260 }} value={draft.outline} onChange={(e) => setDraft({ ...draft, outline: e.target.value })} placeholder="内容大纲…" />
            </Section>
          </div>

          <Section title="Script" description="视频口播、文章主体或完整内容草稿。">
            <textarea className="textarea" style={{ minHeight: 360 }} value={draft.script} onChange={(e) => setDraft({ ...draft, script: e.target.value })} placeholder="完整脚本…" />
          </Section>

          <div className="twoColumns">
            <Section title="Publishing Copy" description="平台发布文案可以先在核心资产中沉淀。">
              <textarea className="textarea" style={{ minHeight: 190 }} value={draft.copywriting} onChange={(e) => setDraft({ ...draft, copywriting: e.target.value })} />
            </Section>
            <Section title="CTA" description="这条内容希望用户下一步做什么？">
              <textarea className="textarea" style={{ minHeight: 190 }} value={draft.cta} onChange={(e) => setDraft({ ...draft, cta: e.target.value })} />
            </Section>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: 12 }}>
            {saved ? <span className="muted">已保存</span> : null}
            <button className="button" type="submit" disabled={saving || !draft.title.trim()}>{saving ? "保存中…" : "保存 Workspace"}</button>
          </div>
        </form>
      )}
    </>
  );
}
