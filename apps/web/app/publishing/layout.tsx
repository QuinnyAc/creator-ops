"use client";

import { useCallback, useEffect, useMemo, useState, type ReactNode } from "react";
import { usePathname } from "next/navigation";

import { EmptyState, ErrorBanner, Section } from "@/components/ui";
import { api } from "@/lib/api";
import type { Platform, PlatformAccount, Publication } from "@/lib/types";

export default function PublishingLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const showAccountManager = pathname === "/publishing";
  const [platforms, setPlatforms] = useState<Platform[]>([]);
  const [accounts, setAccounts] = useState<PlatformAccount[]>([]);
  const [publications, setPublications] = useState<Publication[]>([]);
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
    } catch (err) {
      setError(err instanceof Error ? err.message : "账号管理加载失败");
    }
  }, [showAccountManager]);

  useEffect(() => {
    void load();
  }, [load]);

  const platformMap = useMemo(() => new Map(platforms.map((item) => [item.id, item])), [platforms]);

  async function deleteAccount(account: PlatformAccount) {
    if (!window.confirm(`确定删除账号“${account.name}”吗？删除后无法恢复。`)) return;
    setError("");
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
          {error ? <ErrorBanner message={error} /> : null}
          <Section
            title={`账号管理 · ${accounts.length}`}
            description="可以在这里直接删除平台账号。若账号仍有关联视频，系统会阻止删除并提示先处理对应视频。"
          >
            {accounts.length === 0 ? (
              <EmptyState>还没有平台账号。</EmptyState>
            ) : (
              <div className="dataList">
                {accounts.map((account) => {
                  const platform = platformMap.get(account.platform_id);
                  const videoCount = publications.filter((item) => item.platform_account_id === account.id).length;
                  return (
                    <div className="dataRow" key={account.id}>
                      <div>
                        <div className="dataRowTitle">{account.name}</div>
                        <div className="dataRowMeta">
                          {platform?.name ?? "平台"}{account.handle ? ` · ${account.handle}` : ""} · {videoCount} 条视频记录
                        </div>
                      </div>
                      <button className="button small danger" type="button" onClick={() => void deleteAccount(account)}>
                        删除账号
                      </button>
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
