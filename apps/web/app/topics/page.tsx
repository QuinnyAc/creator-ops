"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";

import { PlusIcon } from "@/components/icons";
import { Badge, EmptyState, ErrorBanner, PageHeader, Section } from "@/components/ui";
import { ApiError, api, patchJson, postJson, putJson } from "@/lib/api";
import type { ContentPillar, Topic, TopicScore } from "@/lib/types";

const SCORE_FIELDS = [
  ["pain_point", "用户痛点"],
  ["search_demand", "搜索需求"],
  ["trend_heat", "当前热度"],
  ["differentiation", "差异化"],
  ["commercial_value", "商业价值"],
  ["production_effort", "制作难度"],
] as const;

type ScoreForm = Record<(typeof SCORE_FIELDS)[number][0], number>;
const DEFAULT_SCORE: ScoreForm = {
  pain_point: 3,
  search_demand: 3,
  trend_heat: 3,
  differentiation: 3,
  commercial_value: 3,
  production_effort: 3,
};

export default function TopicsPage() {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [pillars, setPillars] = useState<ContentPillar[]>([]);
  const [title, setTitle] = useState("");
  const [coreIdea, setCoreIdea] = useState("");
  const [pillarId, setPillarId] = useState("");
  const [goal, setGoal] = useState("growth");
  const [selected, setSelected] = useState<Topic | null>(null);
  const [score, setScore] = useState<ScoreForm>(DEFAULT_SCORE);
  const [savedScore, setSavedScore] = useState<TopicScore | null>(null);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const [nextTopics, nextPillars] = await Promise.all([
        api<Topic[]>("/topics"),
        api<ContentPillar[]>("/content-pillars"),
      ]);
      setTopics(nextTopics);
      setPillars(nextPillars);
      if (selected) {
        setSelected(nextTopics.find((topic) => topic.id === selected.id) ?? null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "选题加载失败");
    }
  }, [selected]);

  useEffect(() => {
    void load();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const pillarMap = useMemo(
    () => new Map(pillars.map((pillar) => [pillar.id, pillar.name])),
    [pillars],
  );

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

  async function openScore(topic: Topic) {
    setSelected(topic);
    setSavedScore(null);
    setScore(DEFAULT_SCORE);
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

  async function saveScore() {
    if (!selected) return;
    setSaving(true);
    setError("");
    try {
      const result = await putJson<TopicScore>(`/topics/${selected.id}/score`, score);
      setSavedScore(result);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "评分保存失败");
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

      <div className="splitGrid">
        <Section title={`选题数据库 · ${topics.length}`} description="Priority 越高，越值得优先进入生产。">
          {topics.length === 0 ? (
            <EmptyState>还没有正式选题。可以从灵感 Inbox 转换，也可以直接创建。</EmptyState>
          ) : (
            <div className="tableWrap">
              <table className="table">
                <thead><tr><th>选题</th><th>内容支柱</th><th>目标</th><th>机会</th><th>Priority</th><th>状态</th><th /></tr></thead>
                <tbody>
                  {topics.map((topic) => (
                    <tr key={topic.id}>
                      <td><div className="tableTitle">{topic.title}</div><div className="dataRowMeta">{topic.core_idea || "未填写核心观点"}</div></td>
                      <td>{topic.pillar_id ? pillarMap.get(topic.pillar_id) ?? "—" : "—"}</td>
                      <td>{topic.goal ?? "—"}</td>
                      <td className="score">{topic.opportunity_score != null ? Number(topic.opportunity_score).toFixed(0) : "—"}</td>
                      <td className={`score ${Number(topic.priority_score ?? 0) >= 70 ? "high" : ""}`}>{topic.priority_score != null ? Number(topic.priority_score).toFixed(0) : "—"}</td>
                      <td>
                        <select className="inlineSelect" value={topic.status} onChange={(e) => void changeStatus(topic, e.target.value)}>
                          {['evaluating','approved','scheduled','in_production','completed','rejected','archived'].map((value) => <option key={value} value={value}>{value}</option>)}
                        </select>
                      </td>
                      <td><button className="button small secondary" onClick={() => void openScore(topic)}>评分</button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </Section>

        <Section title="选题评分" description={selected ? selected.title : "选择一个选题后，在这里判断机会和投入。"}>
          {!selected ? (
            <EmptyState>从左侧选题表点击“评分”。</EmptyState>
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
              <div className="scoreResult">
                <div><span>Opportunity</span><strong>{savedScore ? Number(savedScore.opportunity_score).toFixed(0) : "—"}</strong></div>
                <div><span>Priority</span><strong>{savedScore ? Number(savedScore.priority_score).toFixed(0) : "—"}</strong></div>
              </div>
              <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 14 }}>
                <button className="button" disabled={saving} onClick={() => void saveScore()}>{saving ? "计算中…" : "保存并计算"}</button>
              </div>
              {savedScore ? <div style={{ marginTop: 12 }}><Badge value={Number(savedScore.priority_score) >= 70 ? "approved" : "evaluating"} /></div> : null}
            </>
          )}
        </Section>
      </div>
    </>
  );
}
