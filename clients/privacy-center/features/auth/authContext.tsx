import React, { createContext, useContext, useState, useCallback, ReactNode } from "react";

interface AuthContextType {
  token: string | null;
  isAuthenticated: boolean;
  setToken: (token: string | null) => void;
  clearToken: () => void;
  login: (token: string) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [token, setTokenState] = useState<string | null>(() => {
    // Initialize from localStorage if available (client-side only)
    if (typeof window !== "undefined") {
      return localStorage.getItem("fides_auth_token");
    }
    return null;
  });

  const setToken = useCallback((newToken: string | null) => {
    setTokenState(newToken);
    if (typeof window !== "undefined") {
      if (newToken) {
        localStorage.setItem("fides_auth_token", newToken);
      } else {
        localStorage.removeItem("fides_auth_token");
      }
    }
  }, []);

  const clearToken = useCallback(() => {
    setToken(null);
  }, [setToken]);

  const login = useCallback((newToken: string) => {
    setToken(newToken);
  }, [setToken]);

  const logout = useCallback(() => {
    clearToken();
  }, [clearToken]);

  const isAuthenticated = Boolean(token);

  const value: AuthContextType = {
    token,
    isAuthenticated,
    setToken,
    clearToken,
    login,
    logout,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
