const TOKEN_KEY = "cs_token";
const ROLE_KEY = "cs_role";

export type Role = "VIEWER" | "ADMIN";

export function getToken(): string | null {
  return sessionStorage.getItem(TOKEN_KEY);
}

export function getRole(): Role | null {
  return sessionStorage.getItem(ROLE_KEY) as Role | null;
}

export function setSession(token: string, role: Role): void {
  sessionStorage.setItem(TOKEN_KEY, token);
  sessionStorage.setItem(ROLE_KEY, role);
}

export function clearSession(): void {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(ROLE_KEY);
}
