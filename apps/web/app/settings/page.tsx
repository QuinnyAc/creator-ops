"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";

import { PlusIcon } from "@/components/icons";
import { EmptyState, ErrorBanner, PageHeader, Section } from "@/components/ui";
import { api, downloadApiFile, postJson } from "@/lib/api";
import type { ContentPillar, Tag } from "@/lib/types";

const EXPORTS = [
  { key: "topics", label: "选题 + 评分", path: "/exports/topics.csv", filename: "creator-ops-topics.csv" },
  { key: "contents", label: "内容资产", path: "/exports/contents.csv", filename: "creator-ops-contents.csv" },
  { key: "publications", label: "发布 + 最新数据", path: "/exports/publications.csv", filename: "creator-ops-publications.csv" },
  { key: "reviews", label: "内容复盘", path: "/exports/reviews.csv", filename: "creator-ops-reviews.csv" },
];

export default function SettingsPage() {
  const [pillars, setPillars] = useState<ContentPillar[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [pillarName, setPillarName] = useState("");
  const [pillarDescription, setPillarDescription] = useState("");
  const [tagName, setTagName] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState("");

  const load = useCallback(async () => {
    try {
      const [nextPillars, nextTags] = await Promise.all([
        api<ContentPillar[]>("/content-pillars"),
        api<Tag[]>("/tags"),
      ]);
      setPillars(nextPillars);
      setTags(nextTags);
    } catch (err) {
      setError(err instanceof Error ? err.message : "设置加载失败");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function addPillar(event: FormEvent) {
    event.preventDefault();
    if (!pillarName.trim()) return;
    setSaving(true);
    setError("");
    try {
      await postJson<ContentPillar>("/content-pillars", {
        name: pillarName.trim(),
        description: pillarDescription.trim() || null,
      });
      setPillarName("");
      setPillarDescription("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "内容支柱创建失败");
    } finally {
      setSaving(false);
    }
  }

  async function addTag(event: FormEvent) {
    event.preventDefault();
    if (!tagName.trim()) return;
    setSaving(true);
    setError("");
    try {
      await postJson<Tag>("/tags", { name: tagName.trim() });
      setTagName("");
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "标签创建失败");
    } finally {
      setSaving(false);
    }
  }

  async function remove(path: string) {
    setError("");
    try {
      await api<void>(path, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  }

  async function exportCsv(key: string, path: string, filename: string) {
    setExporting(key);
    setError("");
    try {
      await downloadApiFile(path, filename);
    } catch (err) {
      setError(err instanceof Error ? err.message : "数据导出失败");
    } finally {
      setExporting("");
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="SYSTEM"
        title="工作台设置"
        description="Content Pillar 是长期战略分类；Tag 是灵活描述标签，两者不要混成一件事。"
      />
      {error ? <ErrorBanner message={error} /> : null}

      <div className="twoColumns">
        <Section title="Content Pillars" description="用于长期分析的稳定内容支柱，例如 AI 工具、AI 教程、AI 创业。">
          <form className="formGrid" onSubmit={addPillar} style={{ marginBottom: 16 }}>
            <div className="field">
              <label htmlFor="pillar-name">名称</label>
              <input id="pillar-name" className="input" value={pillarName} onChange={(e) => setPillarName(e.target.value)} />
            </div>
            <div className="field">
              <label htmlFor="pillar-description">说明</label>
              <input id="pillar-description" className="input" value={pillarDescription} onChange={(e) => setPillarDescription(e.target.value)} />
            </div>
            <div className="formActions"><button className="button small" disabled={saving || !pillarName.trim()} type="submit"><PlusIcon width={14} height={14} />新增 Pillar</button></div>
          </form>
          {pillars.length === 0 ? <EmptyState>还没有内容支柱。</EmptyState> : <div className="dataList">{pillars.map((pillar) => <div className="dataRow" key={pillar.id}><div><div className="dataRowTitle">{pillar.name}</div><div className="dataRowMeta">{pillar.description || "无说明"}</div></div><button className="button small danger" onClick={() => void remove(`/content-pillars/${pillar.id}`)}>删除</button></div>)}</div>}
        </Section>

        <Section title="Tags" description="用于主题、形式、场景等灵活分类；不会替代 Content Pillar。">
          <form onSubmit={addTag} style={{ display: "flex", gap: 8, marginBottom: 16 }}>
            <input className="input" value={tagName} onChange={(e) => setTagName(e.target.value)} placeholder="例如：新手、教程、清单" />
            <button className="button" disabled={saving || !tagName.trim()} type="submit"><PlusIcon width={14} height={14} />添加</button>
          </form>
          {tags.length === 0 ? <EmptyState>还没有标签。</EmptyState> : <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>{tags.map((tag) => <button className="button small secondary" title="点击删除" key={tag.id} onClick={() => void remove(`/tags/${tag.id}`)}>#{tag.name} ×</button>)}</div>}
        </Section>
      </div>

      <div style={{ height: 16 }} />

      <Section title="数据导出" description="Creator Ops 不锁定你的运营数据。随时导出 CSV，用于备份、分析或迁移到其他工具。">
        <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
          {EXPORTS.map((item) => (
            <button
              className="button secondary"
              disabled={Boolean(exporting)}
              key={item.key}
              onClick={() => void exportCsv(item.key, item.path, item.filename)}
              type="button"
            >
              {exporting === item.key ? "导出中…" : `导出 ${item.label}`}
            </button>
          ))}
        </div>
        <p className="dataRowMeta" style={{ marginTop: 12 }}>
          CSV 使用 UTF-8 BOM，中文内容可以直接用 Excel、Numbers 或多维表格打开。
        </p>
      </Section>
    </>
  );
}
