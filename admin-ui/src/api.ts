import { getToken } from "./auth";

export class ApiError extends Error {
  constructor(
    public status: number,
    public error: string,
    message: string,
  ) {
    super(message);
  }
}

async function request<T>(base: string, path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Content-Type", "application/json");
  const token = getToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${base}${path}`, { ...init, headers });
  if (!response.ok) {
    let error = "REQUEST_FAILED";
    let message = response.statusText;
    try {
      const body = await response.json();
      error = body.error ?? error;
      message = body.message ?? message;
    } catch {
      /* ignore */
    }
    throw new ApiError(response.status, error, message);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

export const sessionApi = {
  login: (username: string, password: string) =>
    request<{ accessToken: string; role: string; expiresIn: number }>(
      "/session-api",
      "/auth/login",
      { method: "POST", body: JSON.stringify({ username, password }) },
    ),
  listSessions: (userId: number) =>
    request<SessionRow[]>("/session-api", `/users/${userId}/sessions`),
  getSession: (id: number) => request<SessionRow>("/session-api", `/sessions/${id}`),
  getWallet: (userId: number) =>
    request<{ userId: number; balance: number; currency: string }>(
      "/session-api",
      `/users/${userId}/wallet`,
    ),
  topUp: (userId: number, amount: number) =>
    request<{ userId: number; balance: number; currency: string }>(
      "/session-api",
      `/users/${userId}/wallet/top-up`,
      { method: "POST", body: JSON.stringify({ amount }) },
    ),
};

export const stationApi = {
  listConnectors: (stationId: number) =>
    request<ConnectorRow[]>("/station-api", `/stations/${stationId}/connectors`),
};

export type SessionRow = {
  sessionId: number;
  userId: number;
  connectorId: number;
  status: string;
  startedAt: string;
  endedAt: string | null;
  energyKwh: number | null;
  cost: number | null;
  currency: string;
  walletBalanceAfter: number | null;
};

export type ConnectorRow = {
  connectorId: number;
  stationId: number;
  type: string;
  powerKw: number;
  status: string;
  tariff: {
    tariffId: number;
    pricePerKwh: number;
    startFee: number | null;
    currency: string;
  };
};
