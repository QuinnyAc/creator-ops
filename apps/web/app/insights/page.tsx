"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { EmptyState, ErrorBanner, PageHeader, Section, formatDate } from "@/components/ui";
import { api, patchJson, postJson } from "@/lib/api";
import type { Insight } from "@/lib/types";

export default function InsightsPage() {
  const [insights, setInsights] = useState<Insight[]>([]);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [category, setCategory] = useState("learning");
  const [showArchived, setShowArchived] = useState(false);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    setError("");
    try {
      const items = await api<Insight[]>(showArchived ? "/insights" : "/insights?status_filter=active");
      setInsights(items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Playbook 加载失败");
    }
  }, [showArchived]);

  useEffect(() => {
    void load();
  }, [load]);

  async function create(event: FormEvent) {
    event.preventDefault();
    if (!title.trim() || !body.trim()) return;
    setSaving(true);
    setError("");
    try {
      await postJson<Insight>("/insights", {
        title: title.trim(),
        body: body.trim(),
        category: category.trim() || "learning",
      });
      setTitle("");
      setBody("");
      setCategory("learning");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Insight 创建失败");
    } finally {
      setSaving(false);
    }
  }

  async function setStatus(item: Insight, status: "active" | "archived") {
    setError("");
    try {
      await patchJson<Insight>(`/insights/${item.id}`, { status });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Insight 更新失败");
    }
  }

  async function remove(item: Insight) {
    setError("");
    try {
      await api<void>(`/insights/${item.id}`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Insight 删除失败");
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="PLAYBOOK"
        title="Creator Playbook"
        description="把一次复盘变成长期可复用的方法论。以后选题、标题和 AI 建议都应该优先参考这些属于你的经验。"
      />
      {error ? <ErrorBanner message={error} /> : null}

      <div className="splitGrid">
        <form className="formCard" onSubmit={create}>
          <div className="sectionHeading">
            <div><h2>手动沉淀 Insight</h2><p>也可以从“内容复盘”一键把 Learnings 推送到 Playbook。</p></div>
          </div>
          <div className="formGrid">
            <div className="field full">
              <label htmlFor="insight-title">方法论标题</label>
              <input id="insight-title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="例如：教程类内容要优先优化收藏率" />
            </div>
            <div className="field">
              <label htmlFor="insight-category">分类</label>
              <input id="insight-category" className="input" value={category} onChange={(e) => setCategory(e.target.value)} placeholder="learning / title / topic" />
            </div>
            <div className="field full">
              <label htmlFor="insight-body">经验</label>
              <textarea id="insight-body" className="textarea" style={{ minHeight: 180 }} value={body} onChange={(e) => setBody(e.target.value)} placeholder="写成下一次创作可以直接执行的判断规则。" />
            </div>
            <div className="formActions">
              <button className="button" disabled={saving || !title.trim() || !body.trim()} type="submit">{saving ? "保存中…" : "加入 Playbook"}</button>
            </div>
          </div>
        </form>

        <Section title="Playbook 原则" description="Insight 不是日记，而是可复用的创作判断。">
          <div className="dataList">
            <div className="dataRow"><div><div className="dataRowTitle">具体</div><div className="dataRowMeta">不要写“标题要好”，写“数字 + 明确结果的标题在教程内容里更有效”。</div></div></div>
            <div className="dataRow"><div><div className="dataRowTitle">可执行</div><div className="dataRowMeta">下一条内容应该能直接根据这条经验做一个不同的决定。</div></div></div>
            <div className="dataRow"><div><div className="dataRowTitle">可迭代</div><div className="dataRowMeta">新数据出现后，更新、归档或推翻旧经验，而不是无限堆积。</div></div></div>
          </div>
        </Section>
      </div>

      <div style={{ height: 16 }} />

      <Section
        title={`Insights · ${insights.length}`}
        description="长期积累后，这里就是你的 Creator Intelligence 数据底座。"
        action={
          <button className="button small secondary" type="button" onClick={() => setShowArchived((value) => !value)}>
            {showArchived ? "只看 Active" : "显示归档"}
          </button>
        }
      >
        {insights.length === 0 ? (
          <EmptyState>还没有方法论。先完成一次内容复盘，再把 Learnings 沉淀进来。</EmptyState>
        ) : (
          <div className="dataList">
            {insights.map((item) => (
              <div className="dataRow" key={item.id} style={{ alignItems: "flex-start" }}>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
                    <div className="dataRowTitle">{item.title}</div>
                    <span className="badge">{item.category}</span>
                    {item.status === "archived" ? <span className="badge">archived</span> : null}
                  </div>
                  <div style={{ marginTop: 8, whiteSpace: "pre-wrap", lineHeight: 1.65 }}>{item.body}</div>
                  <div className="dataRowMeta" style={{ marginTop: 8 }}>
                    更新 {formatDate(item.updated_at)}{item.source_review_id ? " · 来自内容复盘" : " · 手动创建"}
                  </div>
                </div>
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", justifyContent: "flex-end" }}>
                  {item.status === "active" ? (
                    <button className="button small secondary" type="button" onClick={() => void setStatus(item, "archived")}>归档</button>
                  ) : (
                    <button className="button small secondary" type="button" onClick={() => void setStatus(item, "active")}>恢复</button>
                  )}
                  <button className="button small danger" type="button" onClick={() => void remove(item)}>删除</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </Section>
    </>
  );
}
