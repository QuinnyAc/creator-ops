"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { EmptyState, ErrorBanner, PageHeader, Section } from "@/components/ui";
import { ApiError, api, putJson } from "@/lib/api";
import type { ContentItem, Review } from "@/lib/types";

type ReviewDraft = {
  goal: string;
  expected_outcome: string;
  what_worked: string;
  what_didnt_work: string;
  learnings: string;
  next_action: string;
};

const EMPTY_REVIEW: ReviewDraft = {
  goal: "",
  expected_outcome: "",
  what_worked: "",
  what_didnt_work: "",
  learnings: "",
  next_action: "",
};

export default function ReviewsPage() {
  const [contents, setContents] = useState<ContentItem[]>([]);
  const [selectedId, setSelectedId] = useState("");
  const [draft, setDraft] = useState<ReviewDraft>(EMPTY_REVIEW);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const loadContents = useCallback(async () => {
    try {
      const items = await api<ContentItem[]>("/contents");
      setContents(items);
      const preferred = items.find((item) => item.status === "review") ?? items.find((item) => item.status === "published") ?? items[0];
      setSelectedId((current) => current || preferred?.id || "");
    } catch (err) {
      setError(err instanceof Error ? err.message : "内容加载失败");
    }
  }, []);

  const loadReview = useCallback(async (contentId: string) => {
    if (!contentId) {
      setDraft(EMPTY_REVIEW);
      return;
    }
    setSaved(false);
    try {
      const review = await api<Review>(`/reviews/content/${contentId}`);
      setDraft({
        goal: review.goal ?? "",
        expected_outcome: review.expected_outcome ?? "",
        what_worked: review.what_worked ?? "",
        what_didnt_work: review.what_didnt_work ?? "",
        learnings: review.learnings ?? "",
        next_action: review.next_action ?? "",
      });
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) {
        setDraft(EMPTY_REVIEW);
      } else {
        setError(err instanceof Error ? err.message : "复盘加载失败");
      }
    }
  }, []);

  useEffect(() => {
    void loadContents();
  }, [loadContents]);

  useEffect(() => {
    void loadReview(selectedId);
  }, [selectedId, loadReview]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!selectedId) return;
    setSaving(true);
    setSaved(false);
    setError("");
    try {
      await putJson<Review>(`/reviews/content/${selectedId}`, draft);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "复盘保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="REVIEW"
        title="内容复盘"
        description="把“这条不错”变成结构化经验，让结果真正优化下一轮创作。"
      />
      {error ? <ErrorBanner message={error} /> : null}

      {contents.length === 0 ? (
        <EmptyState>还没有内容可以复盘。</EmptyState>
      ) : (
        <form className="reviewForm" onSubmit={submit}>
          <Section title="选择内容" description="优先复盘已经发布或进入 Review 阶段的内容。">
            <div className="field">
              <label htmlFor="review-content">内容资产</label>
              <select id="review-content" className="select" value={selectedId} onChange={(e) => setSelectedId(e.target.value)}>
                {contents.map((item) => <option key={item.id} value={item.id}>{item.title} · {item.status}</option>)}
              </select>
            </div>
          </Section>

          <div className="twoColumns">
            <Section title="1. 内容目标" description="发布前究竟希望获得什么结果？">
              <textarea className="textarea" value={draft.goal} onChange={(e) => setDraft({ ...draft, goal: e.target.value })} placeholder="例如：以收藏和涨粉为主要目标" />
            </Section>
            <Section title="2. 预期表现" description="记录发布前的判断，避免事后归因偏差。">
              <textarea className="textarea" value={draft.expected_outcome} onChange={(e) => setDraft({ ...draft, expected_outcome: e.target.value })} placeholder="为什么认为它会成功？" />
            </Section>
          </div>

          <div className="twoColumns">
            <Section title="3. 做得好的地方" description="哪些选择值得保留？">
              <textarea className="textarea" style={{ minHeight: 170 }} value={draft.what_worked} onChange={(e) => setDraft({ ...draft, what_worked: e.target.value })} placeholder="标题、开头、结构、案例、发布时间…" />
            </Section>
            <Section title="4. 不足" description="哪些假设没有成立？">
              <textarea className="textarea" style={{ minHeight: 170 }} value={draft.what_didnt_work} onChange={(e) => setDraft({ ...draft, what_didnt_work: e.target.value })} placeholder="具体指出问题，不只写“数据不好”" />
            </Section>
          </div>

          <div className="twoColumns">
            <Section title="5. Learnings" description="从这条内容学到了什么？">
              <textarea className="textarea" style={{ minHeight: 170 }} value={draft.learnings} onChange={(e) => setDraft({ ...draft, learnings: e.target.value })} placeholder="沉淀为可复用的方法论" />
            </Section>
            <Section title="6. Next Action" description="把复盘重新送回下一轮创作。">
              <textarea className="textarea" style={{ minHeight: 170 }} value={draft.next_action} onChange={(e) => setDraft({ ...draft, next_action: e.target.value })} placeholder="继续做系列 / 换角度 / 优化标题 / 停止该方向…" />
            </Section>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: 12 }}>
            {saved ? <span className="muted">复盘已保存</span> : null}
            <button className="button" type="submit" disabled={saving}>{saving ? "保存中…" : "保存复盘"}</button>
          </div>
        </form>
      )}
    </>
  );
}
