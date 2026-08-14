"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { EmptyState, ErrorBanner, PageHeader, Section, formatDate } from "@/components/ui";
import { api, patchJson, postJson } from "@/lib/api";

type IdeaMemo = {
  id: string;
  user_id: string;
  title: string;
  body: string;
  created_at: string;
  updated_at: string;
};

export default function IdeaMemoPage() {
  const [memos, setMemos] = useState<IdeaMemo[]>([]);
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      setMemos(await api<IdeaMemo[]>("/idea-memos"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "备忘录加载失败");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  function resetForm() {
    setTitle("");
    setBody("");
    setEditingId(null);
  }

  function editMemo(memo: IdeaMemo) {
    setEditingId(memo.id);
    setTitle(memo.title);
    setBody(memo.body);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function saveMemo(event: FormEvent) {
    event.preventDefault();
    if (!title.trim() || !body.trim()) return;
    setSaving(true);
    setError("");
    try {
      if (editingId) {
        await patchJson<IdeaMemo>(`/idea-memos/${editingId}`, {
          title: title.trim(),
          body: body.trim(),
        });
      } else {
        await postJson<IdeaMemo>("/idea-memos", {
          title: title.trim(),
          body: body.trim(),
        });
      }
      resetForm();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "备忘录保存失败");
    } finally {
      setSaving(false);
    }
  }

  async function deleteMemo(memo: IdeaMemo) {
    if (!window.confirm(`确定删除备忘录“${memo.title}”吗？删除后无法恢复。`)) return;
    setError("");
    try {
      await api<void>(`/idea-memos/${memo.id}`, { method: "DELETE" });
      if (editingId === memo.id) resetForm();
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "备忘录删除失败");
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="MEMO"
        title="灵感备忘录"
        description="只用于记录视频灵感和文案草稿，不连接选题、内容、发布或其他工作流。"
      />
      {error ? <ErrorBanner message={error} /> : null}

      <form className="formCard" onSubmit={saveMemo} style={{ marginBottom: 16 }}>
        <div className="sectionHeading">
          <div>
            <h2>{editingId ? "修改备忘录" : "记录新灵感"}</h2>
            <p>标题用于快速查找，正文可以直接保存完整视频文案、开头钩子或零散想法。</p>
          </div>
        </div>
        <div className="formGrid">
          <div className="field full">
            <label htmlFor="memo-title">标题</label>
            <input
              id="memo-title"
              className="input"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="例如：前三秒开头创意"
              maxLength={240}
            />
          </div>
          <div className="field full">
            <label htmlFor="memo-body">灵感文案</label>
            <textarea
              id="memo-body"
              className="textarea"
              value={body}
              onChange={(event) => setBody(event.target.value)}
              placeholder="把完整文案、镜头想法、钩子、备注都写在这里……"
              rows={12}
            />
          </div>
          <div className="formActions" style={{ gap: 8 }}>
            <button className="button" type="submit" disabled={saving || !title.trim() || !body.trim()}>
              {saving ? "保存中…" : editingId ? "保存修改" : "保存备忘录"}
            </button>
            {editingId ? (
              <button className="button secondary" type="button" onClick={resetForm}>取消修改</button>
            ) : null}
          </div>
        </div>
      </form>

      <Section title={`文案记录 · ${memos.length}`} description="按最后修改时间排序。每条记录都可以继续修改或删除。">
        {memos.length === 0 ? (
          <EmptyState>还没有备忘录。上面写下第一条视频灵感即可。</EmptyState>
        ) : (
          <div style={{ display: "grid", gap: 12 }}>
            {memos.map((memo) => (
              <article className="formCard" key={memo.id} style={{ marginBottom: 0 }}>
                <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "flex-start", flexWrap: "wrap" }}>
                  <div style={{ minWidth: 240, flex: 1 }}>
                    <div className="dataRowTitle" style={{ fontSize: 15 }}>{memo.title}</div>
                    <div className="dataRowMeta" style={{ marginTop: 5 }}>最后修改：{formatDate(memo.updated_at)}</div>
                  </div>
                  <div style={{ display: "flex", gap: 8 }}>
                    <button className="button small secondary" type="button" onClick={() => editMemo(memo)}>修改</button>
                    <button className="button small danger" type="button" onClick={() => void deleteMemo(memo)}>删除备忘录</button>
                  </div>
                </div>
                <div
                  style={{
                    marginTop: 14,
                    padding: 14,
                    borderRadius: 10,
                    background: "var(--surface-soft)",
                    whiteSpace: "pre-wrap",
                    lineHeight: 1.75,
                    fontSize: 13,
                  }}
                >
                  {memo.body}
                </div>
              </article>
            ))}
          </div>
        )}
      </Section>
    </>
  );
}
