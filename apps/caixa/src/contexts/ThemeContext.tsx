import React, { createContext, useContext, useState, useEffect } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

const THEME_KEY = 'bagplus_caixa_theme';
const AUTO_DARK_HOUR = 18;

function shouldBeDark(): boolean {
  const hour = new Date().getHours();
  return hour >= AUTO_DARK_HOUR;
}

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const stored = localStorage.getItem(THEME_KEY);
    if (stored === 'light' || stored === 'dark') return stored;
    return shouldBeDark() ? 'dark' : 'light';
  });

  // Aplica classe dark no html
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem(THEME_KEY, theme);
  }, [theme]);

  // Verifica automaticamente a cada minuto se passou das 18h
  useEffect(() => {
    const interval = setInterval(() => {
      const stored = localStorage.getItem(THEME_KEY);
      // Só muda automaticamente se não houver preferência manual recente
      // A lógica: se o usuário não tocou no toggle hoje, aplica auto
      const autoKey = 'bagplus_theme_manual';
      const lastManual = localStorage.getItem(autoKey);
      const today = new Date().toDateString();

      if (lastManual !== today) {
        setTheme(shouldBeDark() ? 'dark' : 'light');
      }
    }, 60000);

    return () => clearInterval(interval);
  }, []);

  const toggleTheme = () => {
    // Marca que o usuário escolheu manualmente hoje
    localStorage.setItem('bagplus_theme_manual', new Date().toDateString());
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
}