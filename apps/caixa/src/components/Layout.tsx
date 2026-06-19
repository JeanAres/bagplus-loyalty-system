import { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import HamburgerButton from './HamburgerButton';
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
  ChevronRight,
  Home,
  BookOpen,
  X,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { cn } from '../lib/utils';
import StatusBar from './StatusBar';

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

interface ManualSection {
  id: string;
  icon: React.ElementType;
  title: string;
  content: React.ReactNode;
}

const manualSections: ManualSection[] = [
  {
    id: 'home',
    icon: Home,
    title: 'Home',
    content: (
      <div className="text-sm text-muted-foreground space-y-3 leading-relaxed">
        <div>
          <p className="font-medium text-foreground mb-1">Leitura Rápida</p>
          <p>Escaneie o QR Code — o sistema redireciona automaticamente:</p>
          <ul className="mt-1.5 space-y-1 ml-3">
            <li>🟦 Em estoque → <span className="font-medium text-foreground">Ativar Sacola</span></li>
            <li>🟢 Ativa → <span className="font-medium text-foreground">Registrar Uso</span></li>
            <li>⚫ Devolvida → Mensagem informativa</li>
          </ul>
        </div>
        <div>
          <p className="font-medium text-foreground mb-1">Resumo do Turno</p>
          <p>Exibe contadores do dia (ativações, usos, devoluções) e suas últimas 5 operações.</p>
        </div>
      </div>
    ),
  },
  {
    id: 'clientes',
    icon: UserPlus,
    title: 'Clientes',
    content: (
      <div className="text-sm text-muted-foreground space-y-3 leading-relaxed">
        <div>
          <p className="font-medium text-foreground mb-1">Cadastrar</p>
          <p>Preencha CPF, nome e telefone (opcional) e clique em <span className="font-medium text-foreground">Cadastrar</span>.</p>
        </div>
        <div>
          <p className="font-medium text-foreground mb-1">Buscar</p>
          <p>Busque por CPF ou nome. No resultado:</p>
          <ul className="mt-1.5 space-y-1 ml-3">
            <li><span className="font-medium text-foreground">Aba Dados</span> — telefone, data de cadastro e sacolas ativas. Clique no lápis para editar.</li>
            <li><span className="font-medium text-foreground">Aba Histórico</span> — total gasto, valor médio e linha do tempo de eventos.</li>
          </ul>
        </div>
      </div>
    ),
  },
  {
    id: 'ativar',
    icon: QrCode,
    title: 'Ativar Sacola',
    content: (
      <div className="text-sm text-muted-foreground space-y-1.5 leading-relaxed">
        <p>Vincula uma sacola nova a um cliente.</p>
        <ol className="list-decimal list-inside space-y-1 mt-2">
          <li>Escaneie o QR Code da sacola</li>
          <li>Informe o CPF do cliente</li>
          <li>Clique em <span className="font-medium text-foreground">Ativar Sacola</span></li>
        </ol>
        <p className="text-xs mt-2">💡 Use a Leitura Rápida na Home para pular o passo 1.</p>
      </div>
    ),
  },
  {
    id: 'uso',
    icon: ShoppingBag,
    title: 'Registrar Uso',
    content: (
      <div className="text-sm text-muted-foreground space-y-1.5 leading-relaxed">
        <ol className="list-decimal list-inside space-y-1">
          <li>Escaneie o QR Code da sacola</li>
          <li>Verifique os dados (cliente, utilizações, estado)</li>
          <li>Digite o valor da compra — ex: <code className="text-xs bg-secondary px-1 rounded">2599</code> vira <code className="text-xs bg-secondary px-1 rounded">25,99</code></li>
          <li>Clique em <span className="font-medium text-foreground">Registrar Uso</span></li>
        </ol>
        <div className="mt-2 px-3 py-2 bg-secondary rounded-lg text-xs space-y-0.5">
          <p>⚠️ Valor mínimo: <span className="font-medium text-foreground">R$ 15,00</span></p>
          <p>⚠️ Intervalo mínimo entre usos: <span className="font-medium text-foreground">4 horas</span></p>
        </div>
      </div>
    ),
  },
  {
    id: 'devolucao',
    icon: RotateCcw,
    title: 'Devolver Sacola',
    content: (
      <div className="text-sm text-muted-foreground space-y-2 leading-relaxed">
        <ol className="list-decimal list-inside space-y-1">
          <li>Escaneie o QR Code da sacola</li>
          <li>Confirme os dados e o desconto calculado</li>
          <li>Clique em <span className="font-medium text-foreground">Confirmar Devolução</span></li>
        </ol>
        <p className="text-xs font-medium text-foreground mt-1">Descontos por estado:</p>
        <div className="text-xs space-y-0.5 ml-1">
          <p>🟢 Verde (≤15 usos / ≤60 dias) → <span className="font-medium text-foreground">R$ 40,00</span></p>
          <p>🟡 Amarelo (≤25 usos / ≤80 dias) → <span className="font-medium text-foreground">R$ 20,00</span></p>
          <p>🔴 Vermelho (≤40 usos / ≤90 dias) → <span className="font-medium text-foreground">R$ 10,00</span></p>
          <p>⚫ Expirado → <span className="font-medium text-foreground">R$ 0,00</span></p>
        </div>
        <p className="text-xs mt-1">💡 Aplique o desconto no próximo cupom do cliente.</p>
      </div>
    ),
  },
  {
    id: 'verificar',
    icon: ScanLine,
    title: 'Verificar QR Code',
    content: (
      <div className="text-sm text-muted-foreground leading-relaxed">
        <p>Consulta o status de uma sacola <span className="font-medium text-foreground">sem ativar nem registrar nada</span>.</p>
        <p className="mt-1">Escaneie ou digite o QR Code — o sistema exibe validade, ID e status atual.</p>
      </div>
    ),
  },
  {
    id: 'historico',
    icon: History,
    title: 'Histórico de Usos',
    content: (
      <div className="text-sm text-muted-foreground leading-relaxed">
        <p>Escaneie o QR Code ou digite o ID da sacola (ex: <code className="text-xs bg-secondary px-1 rounded">BAG-00001</code>).</p>
        <p className="mt-1">Exibe total de usos, total gasto, valor médio e a lista cronológica de utilizações.</p>
      </div>
    ),
  },
];

interface LayoutProps {
  children: React.ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [manualOpen, setManualOpen] = useState(false);
  const [openSection, setOpenSection] = useState<string | null>(null);
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

  const toggleSection = (id: string) => {
    setOpenSection((prev) => (prev === id ? null : id));
  };

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
        <div className="flex items-center justify-between px-4 h-14 border-b border-border flex-shrink-0">
          {sidebarOpen && (
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
                <ShoppingBag size={16} className="text-primary-foreground" />
              </div>
              <span className="font-bold text-foreground">Bag+ Caixa</span>
            </div>
          )}
          <HamburgerButton
            isOpen={sidebarOpen}
            onClick={() => setSidebarOpen(!sidebarOpen)}
          />
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
        <header className="bg-card border-b border-border px-6 h-14 flex items-center justify-between flex-shrink-0">
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
          <div className="flex items-center gap-1">
            <button
              onClick={() => setManualOpen(true)}
              className="flex flex-row items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground text-sm"
              title="Manual do Usuário"
            >
              <BookOpen size={16} />
              <span>Manual do usuário</span>
            </button>
            <button
              onClick={toggleTheme}
              className="p-2 rounded-lg hover:bg-secondary transition-colors group"
              title={theme === 'light' ? 'Ativar tema escuro' : 'Ativar tema claro'}
            >
              {theme === 'light'
                ? <Moon size={18} className="text-slate-400 group-hover:text-slate-600 transition-colors" />
                : <Sun size={18} className="text-yellow-400 group-hover:text-yellow-300 transition-colors" />
              }
            </button>
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 overflow-auto p-6">
          {children}
        </main>
        <StatusBar />
      </div>

      {/* Overlay */}
      <div
        className={cn(
          'fixed inset-0 bg-black/40 z-40 transition-opacity duration-300',
          manualOpen ? 'opacity-100 pointer-events-auto' : 'opacity-0 pointer-events-none'
        )}
        onClick={() => setManualOpen(false)}
      />

      {/* Drawer Manual */}
      <div
        className={cn(
          'fixed top-0 right-0 h-full w-80 bg-card border-l border-border z-50 flex flex-col shadow-xl',
          'transition-transform duration-300 ease-in-out',
          manualOpen ? 'translate-x-0' : 'translate-x-full'
        )}
      >
        <div className="flex items-center justify-between px-5 h-14 border-b border-border flex-shrink-0">
          <div className="flex items-center gap-2">
            <BookOpen size={18} className="text-primary" />
            <span className="font-semibold text-foreground">Manual do Usuário</span>
          </div>
          <button
            onClick={() => setManualOpen(false)}
            className="p-1.5 rounded-lg hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground"
          >
            <X size={16} />
          </button>
        </div>
        <div className="flex-1 overflow-y-auto">
          {manualSections.map((section) => {
            const Icon = section.icon;
            const isOpen = openSection === section.id;
            return (
              <div key={section.id} className="border-b border-border">
                <button
                  onClick={() => toggleSection(section.id)}
                  className={cn(
                    'w-full flex items-center justify-between px-5 py-3.5 text-left transition-colors',
                    isOpen ? 'bg-secondary' : 'hover:bg-secondary/60'
                  )}
                >
                  <div className="flex items-center gap-3">
                    <Icon size={16} className={cn(isOpen ? 'text-primary' : 'text-muted-foreground')} />
                    <span className={cn('text-sm font-medium', isOpen ? 'text-foreground' : 'text-muted-foreground')}>
                      {section.title}
                    </span>
                  </div>
                  {isOpen
                    ? <ChevronUp size={14} className="text-muted-foreground flex-shrink-0" />
                    : <ChevronDown size={14} className="text-muted-foreground flex-shrink-0" />
                  }
                </button>
                {isOpen && (
                  <div className="px-5 py-4 bg-background">
                    {section.content}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

    </div>
  );
}