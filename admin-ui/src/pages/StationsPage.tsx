import { useEffect, useState } from "react";
import { ApiError, ConnectorRow, stationApi } from "../api";

function statusClass(status: string): string {
  return `status status-${status.toLowerCase()}`;
}

export function StationsPage() {
  const [rows, setRows] = useState<ConnectorRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await stationApi.listConnectors(1);
        if (!cancelled) setRows(data);
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Failed to load connectors");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Stations</h2>
          <p className="lede">Read-only connectors for station 1 — status and tariff snapshot.</p>
        </div>
      </div>
      {loading && <p className="loading">Loading connectors…</p>}
      {error && <p className="error">{error}</p>}
      {!loading && !error && (
        <div className="grid-cards">
          {rows.map((row) => (
            <article key={row.connectorId} className="connector-card">
              <header>
                <div>
                  <h3>Connector {row.connectorId}</h3>
                  <p className="muted" style={{ margin: "0.2rem 0 0" }}>
                    {row.type} · {row.powerKw} kW
                  </p>
                </div>
                <span className={statusClass(row.status)}>{row.status}</span>
              </header>
              <div className="connector-meta">
                <div>
                  Price / kWh:{" "}
                  <strong>
                    {row.tariff.pricePerKwh} {row.tariff.currency}
                  </strong>
                </div>
                <div>
                  Start fee: <strong>{row.tariff.startFee ?? "—"}</strong>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
