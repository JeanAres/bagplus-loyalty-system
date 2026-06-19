import React, { createContext, useContext, useState, useEffect } from 'react';
import { login as apiLogin, TOKEN_KEY, USER_KEY } from '@bagplus/shared/api';
import type { AuthUser } from '@bagplus/shared/types';

interface AuthContextType {
  user: AuthUser | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (username: string, password: string, terminal: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const storedUser = sessionStorage.getItem(USER_KEY);
    const storedToken = sessionStorage.getItem(TOKEN_KEY);
    if (storedUser && storedToken) {
      try {
        const parsed: AuthUser = JSON.parse(storedUser);
        if (parsed.role === 'caixa') {
          setUser(parsed);
        } else {
          sessionStorage.removeItem(USER_KEY);
          sessionStorage.removeItem(TOKEN_KEY);
        }
      } catch {
        sessionStorage.removeItem(USER_KEY);
        sessionStorage.removeItem(TOKEN_KEY);
      }
    }
    setIsLoading(false);
  }, []);

  const login = async (username: string, password: string, terminal: string) => {
    setIsLoading(true);
    try {
      const response = await apiLogin(username, password, terminal);

      if (response.user.role !== 'caixa') {
        throw new Error('Acesso negado. Este sistema é exclusivo para operadores de caixa.');
      }

      sessionStorage.setItem(TOKEN_KEY, response.access_token);
      sessionStorage.setItem(USER_KEY, JSON.stringify(response.user));
      setUser(response.user);
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    sessionStorage.removeItem(TOKEN_KEY);
    sessionStorage.removeItem(USER_KEY);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
}