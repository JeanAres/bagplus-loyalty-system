import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import {
  QrCode,
  ShoppingBag,
  RotateCcw,
  UserPlus,
  Search,
  ScanLine,
} from 'lucide-react';
import { cn } from '../lib/utils';

interface QuickActionProps {
  icon: React.ElementType;
  label: string;
  href: string;
  color: string;
}

function QuickAction({ icon: Icon, label, href, color }: QuickActionProps) {
  const navigate = useNavigate();
  return (
    <button
      onClick={() => navigate(href)}
      className={cn(
        'flex flex-col items-center justify-center gap-3 p-6 rounded-xl border border-border',
        'hover:scale-[1.02] transition-all duration-200 hover:shadow-md',
        'bg-card text-foreground w-full'
      )}
    >
      <div className={cn('w-12 h-12 rounded-xl flex items-center justify-center', color)}>
        <Icon size={22} className="text-white" />
      </div>
      <span className="text-sm font-medium text-center">{label}</span>
    </button>
  );
}

export default function Home() {
  const { user } = useAuth();

  const quickActions: QuickActionProps[] = [
    { icon: QrCode, label: 'Ativar Sacola', href: '/ativar', color: 'bg-primary' },
    { icon: ShoppingBag, label: 'Registrar Uso', href: '/registrar-uso', color: 'bg-lime-500' },
    { icon: RotateCcw, label: 'Devolver Sacola', href: '/devolucao', color: 'bg-blue-600' },
    { icon: UserPlus, label: 'Cadastrar Cliente', href: '/cadastrar-cliente', color: 'bg-orange-500' },
    { icon: Search, label: 'Buscar Cliente', href: '/buscar-cliente', color: 'bg-purple-600' },
    { icon: ScanLine, label: 'Verificar QR Code', href: '/verificar-qr', color: 'bg-teal-600' },
  ];

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Bom dia' : hour < 18 ? 'Boa tarde' : 'Boa noite';

  return (
    <div className="max-w-2xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-foreground">
          {greeting}, {user?.nome?.split(' ')[0]}!
        </h2>
        <p className="text-muted-foreground mt-1">Selecione uma operação para começar.</p>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {quickActions.map((action) => (
          <QuickAction key={action.href} {...action} />
        ))}
      </div>
    </div>
  );
}