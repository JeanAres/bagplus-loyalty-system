import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import {
  ShoppingBag,
  QrCode,
  RotateCcw,
  UserPlus,
  Search,
  ScanLine,
  History,
  LogOut,
  Moon,
  Sun,
  Menu,
  X,
  ChevronRight,
  Home,
} from 'lucide-react';
import { cn } from '../lib/utils';

interface NavItem {
  icon: React.ElementType;
  label: string;
  href: string;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navSections: NavSection[] = [
  {
    title: 'Clientes',
    items: [
      { icon: UserPlus, label: 'Cadastrar Cliente', href: '/cadastrar-cliente' },
      { icon: Search, label: 'Buscar Cliente', href: '/buscar-cliente' },
    ],
  },
  {
    title: 'Sacolas',
    items: [
      { icon: QrCode, label: 'Ativar Sacola', href: '/ativar' },
      { icon: ShoppingBag, label: 'Registrar Uso', href: '/registrar-uso' },
      { icon: RotateCcw, label: 'Devolver Sacola', href: '/devolucao' },
      { icon: ScanLine, label: 'Verificar QR Code', href: '/verificar-qr' },
      { icon: History, label: 'Histórico de Usos', href: '/historico' },
    ],
  },
];

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const initials = user?.nome
    ? user.nome.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase()
    : 'CX';

  const currentPage = navSections
    .flatMap((s) => s.items)
    .find((i) => i.href === location.pathname);

  return (
    <div className="flex h-screen bg-background">

      {/* Sidebar */}
      <aside
        className={cn(
          'flex flex-col border-r border-border bg-card transition-all duration-300 overflow-hidden',
          sidebarOpen ? 'w-64' : 'w-16'
        )}
      >
        {/* Logo + Toggle */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          {sidebarOpen && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <ShoppingBag size={16} className="text-primary-foreground" />
              </div>
              <span className="font-bold text-foreground">Bag+ Caixa</span>
            </div>
          )}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="p-1.5 rounded-lg hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground"
          >
            {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-4">
          {navSections.map((section) => (
            <div key={section.title}>
              {sidebarOpen && (
                <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-3 mb-2">
                  {section.title}
                </p>
              )}
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.href;
                  return (
                    <button
                      key={item.href}
                      onClick={() => navigate(item.href)}
                      className={cn(
                        'w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors',
                        isActive
                          ? 'bg-primary text-primary-foreground'
                          : 'text-muted-foreground hover:bg-secondary hover:text-foreground'
                      )}
                    >
                      <Icon size={18} className="flex-shrink-0" />
                      {sidebarOpen && <span className="font-medium">{item.label}</span>}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* User + Logout */}
        <div className="p-3 border-t border-border space-y-1">
          <div className={cn('flex items-center gap-2 px-3 py-2 rounded-lg', sidebarOpen ? '' : 'justify-center')}>
            <div className="w-7 h-7 bg-primary rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold text-primary-foreground">{initials}</span>
            </div>
            {sidebarOpen && (
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground truncate">{user?.nome}</p>
                {user?.terminal && (
                  <p className="text-xs text-muted-foreground truncate">{user.terminal}</p>
                )}
              </div>
            )}
          </div>
          <button
            onClick={handleLogout}
            className={cn(
              'w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition-colors',
              'text-destructive hover:bg-destructive/10',
              !sidebarOpen && 'justify-center'
            )}
          >
            <LogOut size={16} className="flex-shrink-0" />
            {sidebarOpen && <span className="font-medium">Sair</span>}
          </button>
        </div>
      </aside>

      {/* Main */}
      <div className="flex-1 flex flex-col overflow-hidden">

        {/* Header */}
        <header className="bg-card border-b border-border px-6 py-3 flex items-center justify-between">
          <nav className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-1 hover:text-foreground transition-colors"
            >
              <Home size={14} />
              Início
            </button>
            {location.pathname !== '/' && (
              <>
                <ChevronRight size={14} />
                <span className="text-foreground font-medium">
                  {currentPage?.label ?? 'Página'}
                </span>
              </>
            )}
          </nav>
          <button
            onClick={toggleTheme}
            className="p-2 rounded-lg hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground"
            title={theme === 'light' ? 'Ativar tema escuro' : 'Ativar tema claro'}
          >
            {theme === 'light' ? <Moon size={18} /> : <Sun size={18} />}
          </button>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
}