"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";

import { EmptyState, ErrorBanner, Section } from "@/components/ui";
import { api } from "@/lib/api";
import type { Platform, PlatformAccount, Publication } from "@/lib/types";

type BilibiliStatus = {
  configured: boolean;
  connected: boolean;
  expires_at: string | null;
  scopes: string[];
  callback_url: string;
};

type AuthorizeUrlResponse = {
  url: string;
  callback_url: string;
};

export default function PublishingLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const showAccountManager = pathname === "/publishing";
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [accounts, setAccounts] = useState<PlatformAccount[]>([]);
  const [publications, setPublications] = useState<Publication[]>([]);
  const [bilibiliStatus, setBilibiliStatus] = useState<Record<string, BilibiliStatus>>({});
  const [connectingId, setConnectingId] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!showAccountManager) return;
    setError("");
    try {
      const [nextPlatforms, nextAccounts, nextPublications] = await Promise.all([
        api<Platform[]>("/platforms"),
        api<PlatformAccount[]>("/platform-accounts"),
        api<Publication[]>("/publications"),
      ]);
      setPlatforms(nextPlatforms);
      setAccounts(nextAccounts);
      setPublications(nextPublications);

      const platformById = new Map(nextPlatforms.map((item) => [item.id, item]));
      const bilibiliAccounts = nextAccounts.filter(
        (account) => platformById.get(account.platform_id)?.slug === "bilibili",
      );
      const statusEntries = await Promise.all(
        bilibiliAccounts.map(async (account) => {
          try {
            const value = await api<BilibiliStatus>(`/platform-accounts/${account.id}/bilibili/status`);
            return [account.id, value] as const;
          } catch {
            return null;
          }
        }),
      );
      setBilibiliStatus(
        Object.fromEntries(statusEntries.filter((item): item is readonly [string, BilibiliStatus] => item !== null)),
      );
    } catch (err) {
      setError(err instanceof Error ? err.message : "账号管理加载失败");
    }
  }, [showAccountManager]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!showAccountManager) return;
    const value = new URLSearchParams(window.location.search).get("bilibili");
    if (value === "connected") {
      setNotice("B站 API 授权成功，现在可以同步该账号的视频数据。\n");
      window.history.replaceState({}, "", "/publishing");
    } else if (value === "error") {
      setError("B站 API 授权没有完成，请检查开放平台应用配置后重新连接。\n");
      window.history.replaceState({}, "", "/publishing");
    }
  }, [showAccountManager]);

  const platformMap = useMemo(() => new Map(platforms.map((item) => [item.id, item])), [platforms]);
  const accountMap = useMemo(() => new Map(accounts.map((item) => [item.id, item])), [accounts]);

  useEffect(() => {
    if (!showAccountManager) return;

    async function autoSyncBilibili() {
      const connectedAccountIds = new Set(
        Object.entries(bilibiliStatus)
          .filter(([, value]) => value.connected)
          .map(([accountId]) => accountId),
      );
      if (connectedAccountIds.size === 0) return;

      const targets = publications.filter((publication) => {
        if (!publication.url || publication.status !== "published") return false;
        if (!connectedAccountIds.has(publication.platform_account_id)) return false;
        const account = accountMap.get(publication.platform_account_id);
        const platform = account ? platformMap.get(account.platform_id) : undefined;
        return platform?.slug === "bilibili";
      });
      if (targets.length === 0) return;

      await Promise.all(
        targets.map((publication) =>
          api<unknown>(`/publications/${publication.id}/sync-metrics`, { method: "POST" }).catch(() => null),
        ),
      );
    }

    const initial = window.setTimeout(() => void autoSyncBilibili(), 8_000);
    const timer = window.setInterval(() => void autoSyncBilibili(), 5 * 60_000);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(timer);
    };
  }, [showAccountManager, bilibiliStatus, publications, accountMap, platformMap]);

  async function connectBilibili(account: PlatformAccount) {
    setConnectingId(account.id);
    setError("");
    setNotice("");
    try {
      const result = await api<AuthorizeUrlResponse>(`/platform-accounts/${account.id}/bilibili/authorize-url`);
      window.location.assign(result.url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "B站 API 连接失败");
      setConnectingId("");
    }
  }

  async function copyCallback(callbackUrl: string) {
    try {
      await navigator.clipboard.writeText(callbackUrl);
      setNotice("B站授权回调地址已复制。\n");
    } catch {
      setError("无法自动复制，请手动选中回调地址复制。\n");
    }
  }

  async function deleteAccount(account: PlatformAccount) {
    if (!window.confirm(`确定删除账号“${account.name}”吗？删除后无法恢复。`)) return;
    setError("");
    setNotice("");
    try {
      await api<void>(`/platform-accounts/${account.id}`, { method: "DELETE" });
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : "账号删除失败");
    }
  }

  return (
    <>
      {children}
      {showAccountManager ? (
        <div style={{ marginTop: 16 }}>
          {notice ? (
            <div style={{ marginBottom: 12, padding: "10px 12px", borderRadius: 10, background: "var(--green-soft)", color: "var(--green)", fontSize: 12 }}>
              {notice.trim()}
            </div>
          ) : null}
          {error ? <ErrorBanner message={error.trim()} /> : null}
          <Section
            title={`账号管理 · ${accounts.length}`}
            description="B站账号可连接官方开放平台 API；连接后，发布管理页面打开期间每 5 分钟自动同步一次已发布视频。小红书暂时继续使用手动数据快照。"
          >
            {accounts.length === 0 ? (
              <EmptyState>还没有平台账号。</EmptyState>
            ) : (
              <div className="dataList">
                {accounts.map((account) => {
                  const platform = platformMap.get(account.platform_id);
                  const videoCount = publications.filter((item) => item.platform_account_id === account.id).length;
                  const apiStatus = bilibiliStatus[account.id];
                  const isBilibili = platform?.slug === "bilibili";
                  return (
                    <div className="dataRow" key={account.id} style={{ alignItems: "flex-start" }}>
                      <div style={{ minWidth: 0 }}>
                        <div className="dataRowTitle">{account.name}</div>
                        <div className="dataRowMeta">
                          {platform?.name ?? "平台"}{account.handle ? ` · ${account.handle}` : ""} · {videoCount} 条视频记录
                        </div>
                        {isBilibili && apiStatus ? (
                          <div style={{ marginTop: 8, display: "grid", gap: 5 }}>
                            <div className="dataRowMeta">
                              API 状态：{apiStatus.connected ? "已连接 · 自动同步已开启" : apiStatus.configured ? "等待账号授权" : "等待配置开放平台凭据"}
                            </div>
                            <div className="dataRowMeta" style={{ overflowWrap: "anywhere" }}>
                              授权回调地址：{apiStatus.callback_url}
                            </div>
                            <button
                              className="button small ghost"
                              type="button"
                              style={{ width: "fit-content" }}
                              onClick={() => void copyCallback(apiStatus.callback_url)}
                            >
                              复制回调地址
                            </button>
                          </div>
                        ) : platform?.slug === "xiaohongshu" ? (
                          <div className="dataRowMeta" style={{ marginTop: 6 }}>数据方式：手动记录作品数据快照</div>
                        ) : null}
                      </div>
                      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
                        {isBilibili && apiStatus ? (
                          <button
                            className="button small"
                            type="button"
                            disabled={!apiStatus.configured || connectingId === account.id}
                            onClick={() => void connectBilibili(account)}
                            title={!apiStatus.configured ? "请先配置 B站开放平台 Client ID 和 App Secret" : undefined}
                          >
                            {connectingId === account.id ? "连接中…" : apiStatus.connected ? "重新授权B站 API" : "连接B站 API"}
                          </button>
                        ) : null}
                        <button className="button small danger" type="button" onClick={() => void deleteAccount(account)}>
                          删除账号
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </Section>
        </div>
      ) : null}
    </>
  );
}
