import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { meuTurno, verificarQrCode } from '@bagplus/shared/api';
import type { MeuTurno } from '@bagplus/shared/api';
import { formatMoney, formatDateTime } from '@bagplus/shared/utils';
import {
  QrCode,
  ShoppingBag,
  RotateCcw,
  ScanLine,
  Loader2,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import { cn } from '../lib/utils';

const acaoConfig: Record<string, { label: string; icon: React.ElementType; color: string }> = {
  ativar_sacola: { label: 'Ativação', icon: QrCode, color: 'text-primary' },
  registrar_uso: { label: 'Uso registrado', icon: ShoppingBag, color: 'text-lime-600 dark:text-lime-400' },
  devolver_sacola: { label: 'Devolução', icon: RotateCcw, color: 'text-blue-600 dark:text-blue-400' },
};

export default function Home() {
  const { user } = useAuth();
  const navigate = useNavigate();

  const [turno, setTurno] = useState<MeuTurno | null>(null);
  const [isLoadingTurno, setIsLoadingTurno] = useState(true);

  const [qrCode, setQrCode] = useState('');
  const [isVerificando, setIsVerificando] = useState(false);
  const [leituraError, setLeituraError] = useState<string | null>(null);
  const [leituraInfo, setLeituraInfo] = useState<string | null>(null);

  useEffect(() => {
    meuTurno()
      .then(setTurno)
      .catch(() => setTurno(null))
      .finally(() => setIsLoadingTurno(false));
  }, []);

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Bom dia' : hour < 18 ? 'Boa tarde' : 'Boa noite';

  const handleLeitura = async (e: React.FormEvent) => {
    e.preventDefault();
    setLeituraError(null);
    setLeituraInfo(null);

    const trimmed = qrCode.trim();
    if (!trimmed) {
      setLeituraError('Escaneie ou digite o QR Code');
      return;
    }

    const partes = trimmed.split(':');
    if (partes.length !== 3 || !partes[0].startsWith('BAG-')) {
      setLeituraError('QR Code inválido. Formato esperado: BAG-00001:2026-05-13:checksum');
      return;
    }

    setIsVerificando(true);
    try {
      const res = await verificarQrCode(trimmed);

      if (!res.valido) {
        setLeituraError(res.erro || 'QR Code inválido');
        return;
      }

      switch (res.status) {
        case 'estoque':
          navigate('/ativar', { state: { qrCode: trimmed } });
          break;
        case 'ativo':
          navigate('/registrar-uso', { state: { qrCode: trimmed, sugerirDevolucao: true } });
          break;
        case 'devolvido':
          setLeituraInfo('Esta sacola já foi devolvida e não pode ser reutilizada.');
          break;
        default:
          setLeituraInfo(`Status da sacola: ${res.status}`);
      }
    } catch (err) {
      setLeituraError(err instanceof Error ? err.message : 'Erro ao verificar QR Code');
    } finally {
      setIsVerificando(false);
    }
  };

  const inputClass = cn(
    'w-full h-10 px-3 rounded-md border bg-input text-foreground placeholder:text-muted-foreground',
    'focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent',
    'disabled:opacity-50 transition-colors text-sm'
  );

  return (
    <div className="max-w-2xl mx-auto space-y-6">

      {/* Saudação */}
      <div>
        <h2 className="text-2xl font-bold text-foreground">
          {greeting}, {user?.nome?.split(' ')[0]}!
        </h2>
        <p className="text-muted-foreground mt-1">Escaneie uma sacola para começar.</p>
      </div>

      {/* Leitura rápida */}
      <div className="bg-card border border-primary rounded-2xl p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center">
            <ScanLine size={20} className="text-primary" />
          </div>
          <div>
            <h3 className="font-semibold text-foreground">Leitura Rápida</h3>
            <p className="text-xs text-muted-foreground">Escaneie o QR Code e seja direcionado automaticamente</p>
          </div>
        </div>

        <form onSubmit={handleLeitura} className="space-y-3">
          <input
            type="text"
            placeholder="BAG-00001:2026-05-13:checksum"
            value={qrCode}
            onChange={(e) => setQrCode(e.target.value)}
            disabled={isVerificando}
            autoFocus
            className={inputClass}
          />

          {leituraError && (
            <div className="px-3 py-2.5 bg-destructive/10 border border-destructive/20 rounded-md">
              <p className="text-destructive text-sm">{leituraError}</p>
            </div>
          )}

          {leituraInfo && (
            <div className="px-3 py-2.5 bg-secondary border border-border rounded-md flex items-center gap-2">
              <AlertCircle size={14} className="text-muted-foreground flex-shrink-0" />
              <p className="text-muted-foreground text-sm">{leituraInfo}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isVerificando || !qrCode.trim()}
            className={cn(
              'w-full h-10 rounded-md bg-primary text-primary-foreground font-medium text-sm',
              'hover:bg-primary/90 transition-colors disabled:opacity-50',
              'flex items-center justify-center gap-2'
            )}
          >
            {isVerificando ? <><Loader2 size={16} className="animate-spin" /> Verificando...</> : 'Continuar'}
          </button>
        </form>
      </div>

      {/* Resumo do turno */}
      <div className="bg-card border border-border rounded-2xl overflow-hidden">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="font-semibold text-foreground">Resumo do Turno</h3>
          <p className="text-xs text-muted-foreground">Suas operações de hoje</p>
        </div>

        {isLoadingTurno ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={24} className="animate-spin text-muted-foreground" />
          </div>
        ) : turno ? (
          <>
            {/* Contadores */}
            <div className="grid grid-cols-3 divide-x divide-border border-b border-border">
              <div className="px-4 py-4 text-center">
                <QrCode size={18} className="text-primary mx-auto mb-1" />
                <p className="text-xl font-bold text-foreground">{turno.resumo.ativacoes}</p>
                <p className="text-xs text-muted-foreground">Ativações</p>
              </div>
              <div className="px-4 py-4 text-center">
                <ShoppingBag size={18} className="text-lime-600 dark:text-lime-400 mx-auto mb-1" />
                <p className="text-xl font-bold text-foreground">{turno.resumo.usos_registrados}</p>
                <p className="text-xs text-muted-foreground">Usos</p>
              </div>
              <div className="px-4 py-4 text-center">
                <RotateCcw size={18} className="text-blue-600 dark:text-blue-400 mx-auto mb-1" />
                <p className="text-xl font-bold text-foreground">{turno.resumo.devolucoes}</p>
                <p className="text-xs text-muted-foreground">Devoluções</p>
              </div>
            </div>

            {/* Últimas ações */}
            {turno.ultimas_acoes.length > 0 ? (
              <div className="divide-y divide-border">
                {turno.ultimas_acoes.map((acao, idx) => {
                  const config = acaoConfig[acao.acao] || { label: acao.acao, icon: CheckCircle, color: 'text-muted-foreground' };
                  const Icon = config.icon;
                  return (
                    <div key={idx} className="px-6 py-3 flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center flex-shrink-0">
                          <Icon size={14} className={config.color} />
                        </div>
                        <div>
                          <p className="text-sm text-foreground font-medium">
                            {config.label}{acao.sacola_id ? ` — ${acao.sacola_id}` : ''}
                          </p>
                          <p className="text-xs text-muted-foreground">{formatDateTime(acao.timestamp)}</p>
                        </div>
                      </div>
                      {acao.valor_compra != null && (
                        <span className="text-sm font-semibold text-foreground">{formatMoney(acao.valor_compra)}</span>
                      )}
                      {acao.desconto_concedido != null && acao.desconto_concedido > 0 && (
                        <span className="text-sm font-semibold text-green-600 dark:text-green-400">
                          {formatMoney(acao.desconto_concedido)}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground py-6 text-center">Nenhuma operação registrada hoje ainda.</p>
            )}
          </>
        ) : (
          <p className="text-sm text-muted-foreground py-6 text-center">Não foi possível carregar o resumo do turno.</p>
        )}
      </div>
    </div>
  );
}