import { useState } from "react";
import { Role, clearSession, getRole, getToken } from "./auth";
import { LoginPage } from "./pages/LoginPage";
import { SessionsPage } from "./pages/SessionsPage";
import { StationsPage } from "./pages/StationsPage";
import { TopUpPage } from "./pages/TopUpPage";

type Screen = "stations" | "sessions" | "topup";

export default function App() {
  const [role, setRole] = useState<Role | null>(() => (getToken() ? getRole() : null));
  const [screen, setScreen] = useState<Screen>("stations");

  if (!role) {
    return (
      <main className="app-login">
        <LoginPage onLoggedIn={setRole} />
      </main>
    );
  }

  return (
    <main className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden />
          ChargeSquare
        </div>
        <nav aria-label="Main">
          <button
            type="button"
            className={`nav-btn${screen === "stations" ? " active" : ""}`}
            onClick={() => setScreen("stations")}
          >
            Stations
          </button>
          <button
            type="button"
            className={`nav-btn${screen === "sessions" ? " active" : ""}`}
            onClick={() => setScreen("sessions")}
          >
            Sessions
          </button>
          <button
            type="button"
            className={`nav-btn${screen === "topup" ? " active" : ""}`}
            onClick={() => setScreen("topup")}
          >
            Top-up
          </button>
        </nav>
        <div className="topbar-right">
          <span className="role-chip">{role}</span>
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => {
              clearSession();
              setRole(null);
            }}
          >
            Log out
          </button>
        </div>
      </header>
      {screen === "stations" && <StationsPage />}
      {screen === "sessions" && <SessionsPage />}
      {screen === "topup" && <TopUpPage isAdmin={role === "ADMIN"} />}
    </main>
  );
}
