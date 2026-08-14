"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { PlusIcon } from "@/components/icons";
import { Badge, EmptyState, ErrorBanner, PageHeader, Section } from "@/components/ui";
import { ApiError, api, patchJson, postJson, putJson } from "@/lib/api";
import type { ContentPillar, Tag, Topic, TopicScore } from "@/lib/types";

const SCORE_FIELDS = [
  ["pain_point", "用户痛点"],
  ["search_demand", "搜索需求"],
  ["trend_heat", "当前热度"],
  ["differentiation", "差异化"],
  ["commercial_value", "商业价值"],
  ["production_effort", "制作难度"],
] as const;

const TOPIC_STATUSES = [
  "evaluating",
  "approved",
  "scheduled",
  "in_production",
  "completed",
  "rejected",
  "archived",
];

type ScoreForm = Record<(typeof SCORE_FIELDS)[number][0], number>;
type TopicLibraryItem = Topic & { tags: Tag[] };

const DEFAULT_SCORE: ScoreForm = {
  pain_point: 3,
  search_demand: 3,
  trend_heat: 3,
  differentiation: 3,
  commercial_value: 3,
  production_effort: 3,
};

export default function TopicsPage() {
  const [topics, setTopics] = useState<TopicLibraryItem[]>([]);
  const [pillars, setPillars] = useState<ContentPillar[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [title, setTitle] = useState("");
  const [coreIdea, setCoreIdea] = useState("");
  const [pillarId, setPillarId] = useState("");
  const [goal, setGoal] = useState("growth");
  const [selected, setSelected] = useState<TopicLibraryItem | null>(null);
  const [score, setScore] = useState<ScoreForm>(DEFAULT_SCORE);
  const [savedScore, setSavedScore] = useState<TopicScore | null>(null);
  const [selectedTagIds, setSelectedTagIds] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [filterPillarId, setFilterPillarId] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [filterTagId, setFilterTagId] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const [nextTopics, nextPillars, nextTags] = await Promise.all([
        api<TopicLibraryItem[]>("/topics"),
        api<ContentPillar[]>("/content-pillars"),
        api<Tag[]>("/tags"),
      ]);
      setTopics(nextTopics);
      setPillars(nextPillars);
      setTags(nextTags);
      setSelected((current) =>
        current ? nextTopics.find((topic) => topic.id === current.id) ?? null : null,
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "选题加载失败");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const pillarMap = useMemo(
    () => new Map(pillars.map((pillar) => [pillar.id, pillar.name])),
    [pillars],
  );

  const filteredTopics = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase();
    return topics.filter((topic) => {
      if (filterPillarId && topic.pillar_id !== filterPillarId) return false;
      if (filterStatus && topic.status !== filterStatus) return false;
      if (filterTagId && !topic.tags.some((tag) => tag.id === filterTagId)) return false;
      if (!normalizedQuery) return true;

      const searchable = [
        topic.title,
        topic.core_idea ?? "",
        topic.target_audience ?? "",
        topic.user_problem ?? "",
        topic.angle ?? "",
        ...topic.tags.map((tag) => tag.name),
      ]
        .join(" ")
        .toLocaleLowerCase();
      return searchable.includes(normalizedQuery);
    });
  }, [filterPillarId, filterStatus, filterTagId, query, topics]);

  const hasFilters = Boolean(query || filterPillarId || filterStatus || filterTagId);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    setError("");
    try {
      await postJson<Topic>("/topics", {
        title: title.trim(),
        core_idea: coreIdea.trim() || null,
        pillar_id: pillarId || null,
        goal,
        planned_platforms: [],
      });
      setTitle("");
      setCoreIdea("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建选题失败");
    } finally {
      setSaving(false);
    }
  }

  async function changeStatus(topic: Topic, status: string) {
    try {
      await patchJson<Topic>(`/topics/${topic.id}`, { status });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "状态更新失败");
    }
  }

  async function openScore(topic: TopicLibraryItem) {
    setSelected(topic);
    setSavedScore(null);
    setScore(DEFAULT_SCORE);
    setSelectedTagIds(topic.tags.map((tag) => tag.id));
    setError("");

    try {
      const existing = await api<TopicScore>(`/topics/${topic.id}/score`);
      setSavedScore(existing);
      setScore({
        pain_point: existing.pain_point,
        search_demand: existing.search_demand,
        trend_heat: existing.trend_heat,
        differentiation: existing.differentiation,
        commercial_value: existing.commercial_value,
        production_effort: existing.production_effort,
      });
    } catch (err) {
      if (!(err instanceof ApiError && err.status === 404)) {
        setError(err instanceof Error ? err.message : "评分加载失败");
      }
    }
  }

  function toggleTag(tagId: string) {
    setSelectedTagIds((current) =>
      current.includes(tagId) ? current.filter((id) => id !== tagId) : [...current, tagId],
    );
  }

  function clearFilters() {
    setQuery("");
    setFilterPillarId("");
    setFilterStatus("");
    setFilterTagId("");
  }

  async function saveDecision() {
    if (!selected) return;
    setSaving(true);
    setError("");
    try {
      const [result] = await Promise.all([
        putJson<TopicScore>(`/topics/${selected.id}/score`, score),
        putJson<Tag[]>(`/topics/${selected.id}/tags`, { tag_ids: selectedTagIds }),
      ]);
      setSavedScore(result);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "评分或标签保存失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="DECIDE"
        title="选题库"
        description="把“我想到一个题”升级成“我知道为什么现在应该做这个题”。"
      />
      {error ? <ErrorBanner message={error} /> : null}

      <form className="formCard" onSubmit={submit}>
        <div className="formGrid three">
          <div className="field">
            <label htmlFor="topic-title">选题标题</label>
            <input id="topic-title" className="input" value={title} onChange={(e) => setTitle(e.target.value)} placeholder="新选题" />
          </div>
          <div className="field">
            <label htmlFor="topic-pillar">内容支柱</label>
            <select id="topic-pillar" className="select" value={pillarId} onChange={(e) => setPillarId(e.target.value)}>
              <option value="">未分类</option>
              {pillars.map((pillar) => <option key={pillar.id} value={pillar.id}>{pillar.name}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="topic-goal">内容目标</label>
            <select id="topic-goal" className="select" value={goal} onChange={(e) => setGoal(e.target.value)}>
              <option value="growth">涨粉</option>
              <option value="reach">曝光</option>
              <option value="save">收藏</option>
              <option value="conversion">转化</option>
              <option value="brand">品牌</option>
            </select>
          </div>
          <div className="field full">
            <label htmlFor="topic-idea">核心观点</label>
            <textarea id="topic-idea" className="textarea" value={coreIdea} onChange={(e) => setCoreIdea(e.target.value)} />
          </div>
          <div className="formActions">
            <button className="button" disabled={!title.trim() || saving} type="submit"><PlusIcon width={16} height={16} />创建选题</button>
          </div>
        </div>
      </form>

      <div className="formCard" style={{ marginBottom: 16 }}>
        <div className="sectionHeading">
          <div>
            <h2>筛选选题</h2>
            <p>按关键词、内容支柱、状态和标签快速找到下一批值得推进的题。</p>
          </div>
          {hasFilters ? <button className="button small secondary" type="button" onClick={clearFilters}>清除筛选</button> : null}
        </div>
        <div className="formGrid four">
          <div className="field">
            <label htmlFor="topic-search">关键词</label>
            <input id="topic-search" className="input" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="标题、观点、用户问题或标签" />
          </div>
          <div className="field">
            <label htmlFor="filter-pillar">内容支柱</label>
            <select id="filter-pillar" className="select" value={filterPillarId} onChange={(event) => setFilterPillarId(event.target.value)}>
              <option value="">全部</option>
              {pillars.map((pillar) => <option key={pillar.id} value={pillar.id}>{pillar.name}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="filter-status">状态</label>
            <select id="filter-status" className="select" value={filterStatus} onChange={(event) => setFilterStatus(event.target.value)}>
              <option value="">全部</option>
              {TOPIC_STATUSES.map((value) => <option key={value} value={value}>{value}</option>)}
            </select>
          </div>
          <div className="field">
            <label htmlFor="filter-tag">标签</label>
            <select id="filter-tag" className="select" value={filterTagId} onChange={(event) => setFilterTagId(event.target.value)}>
              <option value="">全部</option>
              {tags.map((tag) => <option key={tag.id} value={tag.id}>#{tag.name}</option>)}
            </select>
          </div>
        </div>
      </div>

      <div className="splitGrid">
        <Section title={`选题数据库 · ${filteredTopics.length}/${topics.length}`} description="Priority 越高，越值得优先进入生产。">
          {topics.length === 0 ? (
            <EmptyState>还没有正式选题。可以从灵感 Inbox 转换，也可以直接创建。</EmptyState>
          ) : filteredTopics.length === 0 ? (
            <EmptyState>没有符合当前筛选条件的选题。</EmptyState>
          ) : (
            <div className="tableWrap">
              <table className="table">
                <thead><tr><th>选题</th><th>内容支柱</th><th>目标</th><th>机会</th><th>Priority</th><th>状态</th><th /></tr></thead>
                <tbody>
                  {filteredTopics.map((topic) => (
                    <tr key={topic.id}>
                      <td>
                        <div className="tableTitle">{topic.title}</div>
                        <div className="dataRowMeta">{topic.core_idea || "未填写核心观点"}</div>
                        {topic.tags.length > 0 ? (
                          <div style={{ display: "flex", flexWrap: "wrap", gap: 5, marginTop: 6 }}>
                            {topic.tags.map((tag) => <span className="kanbanCount" key={tag.id}>#{tag.name}</span>)}
                          </div>
                        ) : null}
                      </td>
                      <td>{topic.pillar_id ? pillarMap.get(topic.pillar_id) ?? "—" : "—"}</td>
                      <td>{topic.goal ?? "—"}</td>
                      <td className="score">{topic.opportunity_score != null ? Number(topic.opportunity_score).toFixed(0) : "—"}</td>
                      <td className={`score ${Number(topic.priority_score ?? 0) >= 70 ? "high" : ""}`}>{topic.priority_score != null ? Number(topic.priority_score).toFixed(0) : "—"}</td>
                      <td>
                        <select className="inlineSelect" value={topic.status} onChange={(e) => void changeStatus(topic, e.target.value)}>
                          {TOPIC_STATUSES.map((value) => <option key={value} value={value}>{value}</option>)}
                        </select>
                      </td>
                      <td><button className="button small secondary" type="button" onClick={() => void openScore(topic)}>决策</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>

        <Section title="选题决策" description={selected ? selected.title : "选择一个选题后，在这里判断机会、投入和内容标签。"}>
          {!selected ? (
            <EmptyState>从左侧选题表点击“决策”。</EmptyState>
          ) : (
            <>
              <div className="scoreGrid">
                {SCORE_FIELDS.map(([key, label]) => (
                  <div className="rangeField" key={key}>
                    <div><span>{label}</span><strong>{score[key]}</strong></div>
                    <input
                      type="range"
                      min="1"
                      max="5"
                      value={score[key]}
                      onChange={(event) => setScore((current) => ({ ...current, [key]: Number(event.target.value) }))}
                    />
                  </div>
                ))}
              </div>

              <div style={{ marginTop: 16 }}>
                <div className="field">
                  <label>Tags</label>
                  {tags.length === 0 ? (
                    <p className="dataRowMeta">还没有标签，可先到“设置”创建。</p>
                  ) : (
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 7 }}>
                      {tags.map((tag) => {
                        const active = selectedTagIds.includes(tag.id);
                        return (
                          <button
                            className={`button small ${active ? "" : "secondary"}`}
                            key={tag.id}
                            type="button"
                            onClick={() => toggleTag(tag.id)}
                          >
                            #{tag.name}
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              </div>

              <div className="scoreResult">
                <div><span>Opportunity</span><strong>{savedScore ? Number(savedScore.opportunity_score).toFixed(0) : "—"}</strong></div>
                <div><span>Priority</span><strong>{savedScore ? Number(savedScore.priority_score).toFixed(0) : "—"}</strong></div>
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 14 }}>
                <button className="button" type="button" disabled={saving} onClick={() => void saveDecision()}>{saving ? "计算中…" : "保存决策"}</button>
              </div>
              {savedScore ? <div style={{ marginTop: 12 }}><Badge value={Number(savedScore.priority_score) >= 70 ? "approved" : "evaluating"} /></div> : null}
            </>
          )}
        </Section>
      </div>
    </>
  );
}
