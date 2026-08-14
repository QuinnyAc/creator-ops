"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { EmptyState, ErrorBanner, PageHeader, Section, formatNumber } from "@/components/ui";
import { ApiError, api, postJson, putJson } from "@/lib/api";
import type { ContentItem, Insight, Review } from "@/lib/types";

type ReviewDraft = {
  goal: string;
  expected_outcome: string;
  what_worked: string;
  what_didnt_work: string;
  learnings: string;
  next_action: string;
};

type ReviewMetricsSummary = {
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

type ReviewSuggestion = {
  metrics: ReviewMetricsSummary;
  baseline: ReviewMetricsSummary;
  title_patterns: string[];
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
  const [suggestion, setSuggestion] = useState<ReviewSuggestion | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [loadingSuggestion, setLoadingSuggestion] = useState(false);
  const [saved, setSaved] = useState(false);
  const [promoted, setPromoted] = useState(false);

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
      setSuggestion(null);
      return;
    }
    setSaved(false);
    setPromoted(false);
    setSuggestion(null);
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

  async function saveReview() {
    if (!selectedId) return null;
    const review = await putJson<Review>(`/reviews/content/${selectedId}`, draft);
    setSaved(true);
    return review;
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!selectedId) return;
    setSaving(true);
    setSaved(false);
    setPromoted(false);
    setError("");
    try {
      await saveReview();
    } catch (err) {
      setError(err instanceof Error ? err.message : "复盘保存失败");
    } finally {
      setSaving(false);
    }
  }

  async function generateSuggestion() {
    if (!selectedId) return;
    setLoadingSuggestion(true);
    setError("");
    try {
      setSuggestion(await api<ReviewSuggestion>(`/reviews/content/${selectedId}/suggestions`));
    } catch (err) {
      setError(err instanceof Error ? err.message : "数据复盘建议生成失败");
    } finally {
      setLoadingSuggestion(false);
    }
  }

  function applySuggestion() {
    if (!suggestion) return;
    setDraft((current) => ({
      ...current,
      what_worked: suggestion.what_worked,
      what_didnt_work: suggestion.what_didnt_work,
      learnings: suggestion.learnings,
      next_action: suggestion.next_action,
    }));
    setSaved(false);
    setPromoted(false);
  }

  async function promoteToPlaybook() {
    if (!selectedId || !draft.learnings.trim()) return;
    setSaving(true);
    setError("");
    setPromoted(false);
    try {
      await saveReview();
      const content = contents.find((item) => item.id === selectedId);
      await postJson<Insight>(`/insights/from-content/${selectedId}`, {
        title: content ? `${content.title} · 核心经验` : undefined,
        category: "content-learning",
      });
      setPromoted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "沉淀到 Playbook 失败");
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

          <Section
            title="数据辅助复盘"
            description="透明规则引擎会比较该内容与账号整体基线，并识别标题模式；建议只是初稿，不会自动覆盖人工判断。"
            action={<button className="button small secondary" type="button" disabled={loadingSuggestion} onClick={() => void generateSuggestion()}>{loadingSuggestion ? "分析中…" : "生成数据建议"}</button>}
          >
            {!suggestion ? (
              <EmptyState>点击“生成数据建议”，系统会读取该 Content 各 Publication 的最新快照。</EmptyState>
            ) : (
              <>
                <div className="metricGrid">
                  <div className="metricBox"><span>平均浏览</span><strong>{formatNumber(Math.round(suggestion.metrics.avg_views))}</strong><div className="dataRowMeta">基线 {formatNumber(Math.round(suggestion.baseline.avg_views))}</div></div>
                  <div className="metricBox"><span>互动率</span><strong>{suggestion.metrics.engagement_rate}%</strong><div className="dataRowMeta">基线 {suggestion.baseline.engagement_rate}%</div></div>
                  <div className="metricBox"><span>收藏率</span><strong>{suggestion.metrics.favorite_rate}%</strong><div className="dataRowMeta">基线 {suggestion.baseline.favorite_rate}%</div></div>
                  <div className="metricBox"><span>转粉率</span><strong>{suggestion.metrics.follower_conversion_rate}%</strong><div className="dataRowMeta">基线 {suggestion.baseline.follower_conversion_rate}%</div></div>
                </div>
                <div className="dataRowMeta" style={{ marginTop: 12 }}>
                  {suggestion.metrics.publications} 个有数据的发布实例 · 标题模式：{suggestion.title_patterns.join("、") || "未识别"}
                </div>
                <div style={{ display: "grid", gap: 10, marginTop: 14 }}>
                  <div className="dataRow"><div><div className="dataRowTitle">做得好的地方</div><div style={{ whiteSpace: "pre-wrap", marginTop: 5 }}>{suggestion.what_worked}</div></div></div>
                  <div className="dataRow"><div><div className="dataRowTitle">可能的不足</div><div style={{ whiteSpace: "pre-wrap", marginTop: 5 }}>{suggestion.what_didnt_work}</div></div></div>
                  <div className="dataRow"><div><div className="dataRowTitle">建议 Learnings</div><div style={{ whiteSpace: "pre-wrap", marginTop: 5 }}>{suggestion.learnings}</div></div></div>
                  <div className="dataRow"><div><div className="dataRowTitle">建议 Next Action</div><div style={{ whiteSpace: "pre-wrap", marginTop: 5 }}>{suggestion.next_action}</div></div></div>
                </div>
                <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 12 }}>
                  <button className="button small" type="button" onClick={applySuggestion}>填入复盘草稿</button>
                </div>
              </>
            )}
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
            <Section title="5. Learnings" description="从这条内容学到了什么？可以一键沉淀到 Creator Playbook。">
              <textarea className="textarea" style={{ minHeight: 170 }} value={draft.learnings} onChange={(e) => { setDraft({ ...draft, learnings: e.target.value }); setPromoted(false); }} placeholder="沉淀为可复用的方法论" />
            </Section>
            <Section title="6. Next Action" description="把复盘重新送回下一轮创作。">
              <textarea className="textarea" style={{ minHeight: 170 }} value={draft.next_action} onChange={(e) => setDraft({ ...draft, next_action: e.target.value })} placeholder="继续做系列 / 换角度 / 优化标题 / 停止该方向…" />
            </Section>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            {saved ? <span className="muted">复盘已保存</span> : null}
            {promoted ? <span className="muted">已沉淀到 Creator Playbook</span> : null}
            <button className="button secondary" type="button" disabled={saving || !draft.learnings.trim()} onClick={() => void promoteToPlaybook()}>
              沉淀到 Playbook
            </button>
            <button className="button" type="submit" disabled={saving}>{saving ? "保存中…" : "保存复盘"}</button>
          </div>
        </form>
      )}
    </>
  );
}
