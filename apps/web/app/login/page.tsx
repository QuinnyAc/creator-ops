"use client";

import { FormEvent, useState } from "react";

import { ErrorBanner } from "@/components/ui";
import { postJson } from "@/lib/api";
import { setAccessToken } from "@/lib/auth";

type AuthResponse = {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    email: string;
    display_name: string;
    timezone: string;
  };
};

export default function LoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const result = await postJson<AuthResponse>(
        mode === "login" ? "/auth/login" : "/auth/register",
        mode === "login"
          ? { email, password }
          : { email, password, display_name: displayName, timezone: "Asia/Shanghai" },
      );
      setAccessToken(result.access_token);
      window.location.assign("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "认证失败");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div style={{ width: "min(100%, 460px)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 20 }}>
        <div className="brandMark">CO</div>
        <div>
          <div className="eyebrow">CREATOR OPERATIONS</div>
          <strong style={{ fontSize: 18 }}>Creator Ops</strong>
        </div>
      </div>

      <div className="formCard" style={{ marginBottom: 0, padding: 26 }}>
        <div className="sectionHeading">
          <div>
            <h2 style={{ fontSize: 22 }}>{mode === "login" ? "登录工作台" : "创建创作者账号"}</h2>
            <p>{mode === "login" ? "使用你的 Creator Ops 账号继续运营。" : "账号数据会与其他创作者隔离。"}</p>
          </div>
        </div>
        {error ? <ErrorBanner message={error} /> : null}
        <form className="formGrid" onSubmit={submit}>
          {mode === "register" ? (
            <div className="field full">
              <label htmlFor="auth-name">显示名称</label>
              <input id="auth-name" className="input" value={displayName} onChange={(e) => setDisplayName(e.target.value)} autoComplete="name" />
            </div>
          ) : null}
          <div className="field full">
            <label htmlFor="auth-email">Email</label>
            <input id="auth-email" className="input" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
          </div>
          <div className="field full">
            <label htmlFor="auth-password">密码</label>
            <input id="auth-password" className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete={mode === "login" ? "current-password" : "new-password"} minLength={mode === "register" ? 8 : 1} />
          </div>
          <div className="formActions" style={{ justifyContent: "space-between", alignItems: "center" }}>
            <button
              className="button ghost"
              type="button"
              onClick={() => {
                setMode((current) => current === "login" ? "register" : "login");
                setError("");
              }}
            >
              {mode === "login" ? "没有账号？注册" : "已有账号？登录"}
            </button>
            <button className="button" type="submit" disabled={saving || !email || !password || (mode === "register" && !displayName.trim())}>
              {saving ? "处理中…" : mode === "login" ? "登录" : "创建账号"}
            </button>
          </div>
        </form>
      </div>

      <p className="dataRowMeta" style={{ marginTop: 12, lineHeight: 1.6 }}>
        本地开发默认仍允许匿名单用户模式；公开部署请在前后端同时开启强制认证配置。
      </p>
    </div>
  );
}
