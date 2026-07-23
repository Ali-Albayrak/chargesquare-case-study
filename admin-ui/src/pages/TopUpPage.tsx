import { FormEvent, useEffect, useState } from "react";
import { ApiError, sessionApi } from "../api";

const DEMO_USER_ID = 7;

type Props = {
  isAdmin: boolean;
};

export function TopUpPage({ isAdmin }: Props) {
  const [balance, setBalance] = useState<number | null>(null);
  const [currency, setCurrency] = useState("TRY");
  const [amount, setAmount] = useState("50");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ok, setOk] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const wallet = await sessionApi.getWallet(DEMO_USER_ID);
        if (!cancelled) {
          setBalance(wallet.balance);
          setCurrency(wallet.currency);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof ApiError ? err.message : "Failed to load wallet");
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setOk(null);
    setError(null);
    const value = Number(amount);
    if (!Number.isFinite(value) || value <= 0) {
      setError("Amount must be greater than 0");
      return;
    }
    setSubmitting(true);
    try {
      const wallet = await sessionApi.topUp(DEMO_USER_ID, value);
      setBalance(wallet.balance);
      setCurrency(wallet.currency);
      setOk(`Topped up. New balance: ${wallet.balance} ${wallet.currency}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Top-up failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <section className="panel">
      <div className="panel-head">
        <div>
          <h2>Wallet top-up</h2>
          <p className="lede">Credit seed user {DEMO_USER_ID}. ADMIN only — API still returns 403 for VIEWER.</p>
        </div>
      </div>

      {loading && <p className="loading">Loading wallet…</p>}
      {!loading && balance != null && (
        <div className="balance-hero">
          <div>
            <p className="label">Current balance</p>
            <p className="value">
              {balance} {currency}
            </p>
          </div>
        </div>
      )}

      {!isAdmin && (
        <p className="banner banner-warn">
          Signed in as VIEWER — top-up controls are hidden. Backend would reject writes with 403.
        </p>
      )}

      {isAdmin && (
        <form onSubmit={onSubmit} className="stack">
          <label>
            Amount ({currency})
            <input
              type="number"
              min="0.01"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
            />
          </label>
          {error && <p className="error">{error}</p>}
          {ok && <p className="ok">{ok}</p>}
          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "Submitting…" : "Top up wallet"}
          </button>
        </form>
      )}
      {!isAdmin && error && <p className="error">{error}</p>}
    </section>
  );
}
