import { FormEvent, useState } from "react";
import { ApiError, sessionApi } from "../api";
import { Role, setSession } from "../auth";

type Props = {
  onLoggedIn: (role: Role) => void;
};

export function LoginPage({ onLoggedIn }: Props) {
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const result = await sessionApi.login(username, password);
      const role = result.role as Role;
      setSession(result.accessToken, role);
      onLoggedIn(role);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-shell">
      <section className="panel login-panel">
        <p className="login-kicker">ChargeSquare Admin</p>
        <h1 className="login-brand">Welcome back</h1>
        <p className="lede">Sign in to monitor stations, review sessions, and top up wallets.</p>
        <form onSubmit={onSubmit} className="stack" style={{ marginTop: "1.25rem" }}>
          <label>
            Username
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="current-password"
            />
          </label>
          {error && <p className="error">{error}</p>}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Signing in…" : "Sign in"}
          </button>
        </form>
        <div className="login-hints">
          <span className="hint-chip">admin / admin</span>
          <span className="hint-chip">viewer / viewer</span>
        </div>
      </section>
    </div>
  );
}
