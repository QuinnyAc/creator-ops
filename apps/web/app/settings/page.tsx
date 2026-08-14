"use client";

import { ChangeEvent, FormEvent, useCallback, useEffect, useState } from "react";

import { PlusIcon } from "@/components/icons";
import { EmptyState, ErrorBanner, PageHeader, Section } from "@/components/ui";
import { api, downloadApiFile, postJson } from "@/lib/api";
import type { ContentPillar, Tag } from "@/lib/types";

const EXPORTS = [
  { key: "topics", label: "选题 + 评分", path: "/exports/topics.csv", filename: "creator-ops-topics.csv" },
  { key: "contents", label: "内容资产", path: "/exports/contents.csv", filename: "creator-ops-contents.csv" },
  { key: "publications", label: "发布 + 最新数据", path: "/exports/publications.csv", filename: "creator-ops-publications.csv" },
  { key: "reviews", label: "内容复盘", path: "/exports/reviews.csv", filename: "creator-ops-reviews.csv" },
  { key: "insights", label: "Creator Playbook", path: "/exports/insights.csv", filename: "creator-ops-insights.csv" },
];

const TIMEZONES = [
  "Asia/Shanghai",
  "Asia/Hong_Kong",
  "Asia/Singapore",
  "Asia/Tokyo",
  "UTC",
  "Europe/London",
  "America/New_York",
  "America/Los_Angeles",
];

type MetricImportResult = {
  imported: number;
  updated: number;
  skipped: number;
  errors: string[];
};

type AuthUser = {
  id: string;
  email: string;
  display_name: string;
  timezone: string;
  created_at: string;
  updated_at: string;
};

export default function SettingsPage() {
  const [profile, setProfile] = useState<AuthUser | null>(null);
  const [displayName, setDisplayName] = useState("");
  const [timezone, setTimezone] = useState("Asia/Shanghai");
  const [pillars, setPillars] = useState<ContentPillar[]>([]);
  const [tags, setTags] = useState<Tag[]>([]);
  const [pillarName, setPillarName] = useState("");
  const [pillarDescription, setPillarDescription] = useState("");
  const [tagName, setTagName] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileSaved, setProfileSaved] = useState(false);
  const [exporting, setExporting] = useState("");
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<MetricImportResult | null>(null);

  const load = useCallback(async () => {
    try {
      const [nextProfile, nextPillars, nextTags] = await Promise.all([
        api<AuthUser>("/auth/me"),
        api<ContentPillar[]>("/content-pillars"),
        api<Tag[]>("/tags"),
      ]);
      setProfile(nextProfile);
      setDisplayName(nextProfile.display_name);
      setTimezone(nextProfile.timezone);
      setPillars(nextPillars);
      setTags(nextTags);
    } catch (err) {
      setError(err instanceof Error ? err.message : "设置加载失败");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function saveProfile(event: FormEvent) {
    event.preventDefault();
    if (!displayName.trim() || !timezone.trim()) return;
    setProfileSaving(true);
    setProfileSaved(false);
    setError("");
    try {
      const nextProfile = await api<AuthUser>("/auth/me", {
        method: "PATCH",
        body: JSON.stringify({
          display_name: displayName.trim(),
          timezone: timezone.trim(),
        }),
      });
      setProfile(nextProfile);
      setDisplayName(nextProfile.display_name);
      setTimezone(nextProfile.timezone);
      setProfileSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Creator Profile 保存失败");
    } finally {
      setProfileSaving(false);
    }
  }

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

  async function importMetrics(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    setImporting(true);
    setImportResult(null);
    setError("");
    try {
      const csvText = await file.text();
      const result = await api<MetricImportResult>("/imports/metrics.csv", {
        method: "POST",
        headers: { "Content-Type": "text/csv" },
        body: csvText,
      });
      setImportResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "指标 CSV 导入失败");
    } finally {
      setImporting(false);
      event.target.value = "";
    }
  }

  return (
    <>
      <PageHeader
        eyebrow="SYSTEM"
        title="工作台设置"
        description="配置创作者身份、时区、Content Pillars、Tags 和数据迁移能力。"
      />
      {error ? <ErrorBanner message={error} /> : null}

      <Section
        title="Creator Profile"
        description="这里的时区是 Creator Ops 的工作台时区来源，为发布日历、计划发布时间和后续自动化提供统一上下文。"
      >
        <form className="formGrid three" onSubmit={saveProfile}>
          <div className="field">
            <label htmlFor="profile-name">显示名称</label>
            <input
              id="profile-name"
              className="input"
              value={displayName}
              onChange={(event) => {
                setDisplayName(event.target.value);
                setProfileSaved(false);
              }}
            />
          </div>
          <div className="field">
            <label htmlFor="profile-email">邮箱</label>
            <input id="profile-email" className="input" value={profile?.email ?? ""} disabled readOnly />
          </div>
          <div className="field">
            <label htmlFor="profile-timezone">工作台时区</label>
            <select
              id="profile-timezone"
              className="select"
              value={timezone}
              onChange={(event) => {
                setTimezone(event.target.value);
                setProfileSaved(false);
              }}
            >
              {!TIMEZONES.includes(timezone) && timezone ? <option value={timezone}>{timezone}</option> : null}
              {TIMEZONES.map((item) => <option key={item} value={item}>{item}</option>)}
            </select>
          </div>
          <div className="formActions">
            {profileSaved ? <span className="muted">Profile 已保存</span> : null}
            <button className="button" disabled={profileSaving || !displayName.trim() || !timezone.trim()} type="submit">
              {profileSaving ? "保存中…" : "保存 Profile"}
            </button>
          </div>
        </form>
        <p className="dataRowMeta" style={{ marginTop: 12 }}>
          当前日期输入仍由浏览器负责本地展示；工作台时区已经持久化，后续日历格式化和平台定时发布会以它为统一来源。
        </p>
      </Section>

      <div style={{ height: 16 }} />

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

      <div className="twoColumns">
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

        <Section title="批量导入数据快照" description="从平台后台或表格整理后，一次导入多条 Publication 指标。相同 publication_id + captured_at 会更新而不是重复创建。">
          <div className="field">
            <label htmlFor="metrics-csv">选择 CSV 文件</label>
            <input id="metrics-csv" className="input" type="file" accept=".csv,text/csv" disabled={importing} onChange={(event) => void importMetrics(event)} />
          </div>
          <div className="dataRowMeta" style={{ marginTop: 10, lineHeight: 1.6 }}>
            必填列：publication_id, captured_at。可选列：views, likes, comments, favorites, shares, followers_gained, extra_metrics。
          </div>
          {importing ? <p className="muted" style={{ marginTop: 12 }}>正在导入…</p> : null}
          {importResult ? (
            <div className="dataList" style={{ marginTop: 14 }}>
              <div className="dataRow"><div><div className="dataRowTitle">导入完成</div><div className="dataRowMeta">新增 {importResult.imported} · 更新 {importResult.updated} · 跳过 {importResult.skipped}</div></div></div>
              {importResult.errors.slice(0, 5).map((message) => <div className="dataRow" key={message}><div className="dataRowMeta">{message}</div></div>)}
            </div>
          ) : null}
        </Section>
      </div>
    </>
  );
}
