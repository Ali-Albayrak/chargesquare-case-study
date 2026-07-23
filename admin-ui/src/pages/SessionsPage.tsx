import { useEffect, useState } from "react";
import { ApiError, SessionRow, sessionApi } from "../api";

const DEMO_USER_ID = 7;

function statusClass(status: string): string {
  return `status status-${status.toLowerCase()}`;
}

export function SessionsPage() {
  const [rows, setRows] = useState<SessionRow[]>([]);
  const [selected, setSelected] = useState<SessionRow | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await sessionApi.listSessions(DEMO_USER_ID);
        if (!cancelled) setRows(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Failed to load sessions");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function openReceipt(id: number) {
    setError(null);
    try {
      const detail = await sessionApi.getSession(id);
      setSelected(detail);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load session");
    }
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Sessions</h2>
          <p className="lede">Charging history for seed user {DEMO_USER_ID}.</p>
        </div>
      </div>
      {loading && <p className="loading">Loading sessions…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && rows.length === 0 && <p className="empty">No sessions yet.</p>}
      {!loading && rows.length > 0 && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Connector</th>
                <th>Status</th>
                <th>Cost</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.sessionId}>
                  <td className="mono">{row.sessionId}</td>
                  <td className="mono">{row.connectorId}</td>
                  <td>
                    <span className={statusClass(row.status)}>{row.status}</span>
                  </td>
                  <td className="mono">
                    {row.cost != null ? `${row.cost} ${row.currency}` : "—"}
                  </td>
                  <td>
                    <button type="button" className="btn-text" onClick={() => openReceipt(row.sessionId)}>
                      Receipt
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {selected && (
        <aside className="receipt">
          <h3>Receipt #{selected.sessionId}</h3>
          <dl>
            <dt>Status</dt>
            <dd>{selected.status}</dd>
            <dt>Energy</dt>
            <dd>{selected.energyKwh ?? "—"} kWh</dd>
            <dt>Cost</dt>
            <dd>
              {selected.cost ?? "—"} {selected.currency}
            </dd>
            <dt>Wallet after</dt>
            <dd>{selected.walletBalanceAfter ?? "—"}</dd>
          </dl>
          <button type="button" className="btn btn-ghost" onClick={() => setSelected(null)}>
            Close
          </button>
        </aside>
      )}
    </section>
  );
}
