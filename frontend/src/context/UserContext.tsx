import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { getStoredUser, clearSession } from "../auth";
import {
  restoreArenaSession, consumeOAuthCallbackParams,
  insforge, fetchArenaProfile, mapInsforgeUser,
} from "../lib/insforge";
import type { User } from "../types";

interface UserCtx {
  user: User | null;
  setUser: (u: User | null) => void;
  logout: () => void;
  refreshRole: () => Promise<void>;
  authError: string | null;
}

const Ctx = createContext<UserCtx>({
  user: null,
  setUser: () => {},
  logout: () => {},
  refreshRole: async () => {},
  authError: null,
});

export function UserProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(getStoredUser());
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    restoreArenaSession()
      .then(({ user: u, error }) => {
        if (u) setUser(u);
        if (error) setAuthError(error);
        consumeOAuthCallbackParams();
      })
      .catch((e) => setAuthError(String(e)));
  }, []);

  const logout = () => {
    clearSession();
    setUser(null);
  };

  const refreshRole = async () => {
    const { data } = await insforge.auth.getCurrentUser();
    if (!data?.user) return;
    const profile = await fetchArenaProfile(data.user.id);
    setUser(mapInsforgeUser(data.user, profile));
  };

  return (
    <Ctx.Provider value={{ user, setUser, logout, refreshRole, authError }}>
      {children}
    </Ctx.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useUser() {
  return useContext(Ctx);
}
