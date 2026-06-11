import { useState } from 'react';
import { devolverSacola, buscarSacola } from '@bagplus/shared/api';
import { formatMoney } from '@bagplus/shared/utils';
import type { Sacola } from '@bagplus/shared/types';
import { RotateCcw, CheckCircle, Loader2, QrCode, AlertTriangle } from 'lucide-react';
import { cn } from '../lib/utils';

type Step = 'qrcode' | 'confirmar' | 'success';

const estadoConfig = {
  verde:    { label: 'Verde',    color: 'text-green-600 dark:text-green-400',   bg: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' },
  amarelo:  { label: 'Amarelo',  color: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800' },
  vermelho: { label: 'Vermelho', color: 'text-red-600 dark:text-red-400',       bg: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800' },
  expirado: { label: 'Expirado', color: 'text-destructive',                     bg: 'bg-destructive/10 border-destructive/20' },
};

interface ResultadoDevolucao {
  mensagem: string;
  sacola: { id: string; utilizacoes: number; dias_de_uso: number; estado: string };
  desconto_concedido: number;
}

export default function Devolucao() {
  const [step, setStep] = useState<Step>('qrcode');
  const [qrCode, setQrCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isBuscando, setIsBuscando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sacola, setSacola] = useState<Sacola | null>(null);
  const [resultado, setResultado] = useState<ResultadoDevolucao | null>(null);

  const handleQrCodeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!qrCode.trim()) {
      setError('Escaneie ou digite o QR Code da sacola');
      return;
    }

    const partes = qrCode.trim().split(':');
    if (partes.length !== 3 || !partes[0].startsWith('BAG-')) {
      setError('QR Code inválido. Formato esperado: BAG-00001:2026-05-13:checksum');
      return;
    }

    setIsBuscando(true);
    try {
      const sacolaId = partes[0];
      const info = await buscarSacola(sacolaId);

      if (info.status !== 'ativo') {
        setError(`Sacola não está ativa. Status atual: ${info.status}`);
        return;
      }

      setSacola(info);
      setStep('confirmar');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sacola não encontrada');
    } finally {
      setIsBuscando(false);
    }
  };

  const handleDevolver = async () => {
    if (!sacola) return;
    setError(null);
    setIsLoading(true);
    try {
      const res = await devolverSacola(sacola.id);
      setResultado(res);
      setStep('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao processar devolução');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNova = () => {
    setStep('qrcode');
    setQrCode('');
    setSacola(null);
    setResultado(null);
    setError(null);
  };

  const inputClass = cn(
    'w-full h-10 px-3 rounded-md border bg-input text-foreground placeholder:text-muted-foreground',
    'focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent',
    'disabled:opacity-50 transition-colors text-sm'
  );

  // Tela de sucesso
  if (step === 'success' && resultado) {
    return (
      <div className="max-w-md mx-auto">
        <div className="bg-card border border-border rounded-2xl p-8 text-center">
          <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} className="text-green-600 dark:text-green-400" />
          </div>
          <h2 className="text-xl font-bold text-foreground mb-1">Sacola devolvida!</h2>
          <p className="text-muted-foreground text-sm mb-6">{resultado.mensagem}</p>

          <div className="bg-secondary rounded-xl p-4 text-left mb-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Sacola</span>
              <span className="font-medium text-foreground">{resultado.sacola.id}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Utilizações</span>
              <span className="font-medium text-foreground">{resultado.sacola.utilizacoes}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Dias de uso</span>
              <span className="font-medium text-foreground">{resultado.sacola.dias_de_uso}</span>
            </div>
          </div>

          {resultado.desconto_concedido > 0 ? (
            <div className="px-4 py-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl mb-6">
              <p className="text-sm text-green-700 dark:text-green-300 font-medium">
                💰 Desconto concedido: {formatMoney(resultado.desconto_concedido)}
              </p>
            </div>
          ) : (
            <div className="px-4 py-3 bg-secondary rounded-xl mb-6">
              <p className="text-sm text-muted-foreground">Sacola expirada — sem desconto de devolução.</p>
            </div>
          )}

          <button
            onClick={handleNova}
            className="w-full h-10 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Processar outra devolução
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto space-y-4">

      {/* Step 1 — QR Code */}
      <div className={cn(
        'bg-card border rounded-2xl p-6 transition-all',
        step === 'qrcode' ? 'border-primary shadow-sm' : 'border-border opacity-60'
      )}>
        <div className="flex items-center gap-3 mb-5">
          <div className={cn(
            'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold',
            step === 'qrcode' ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground'
          )}>1</div>
          <div>
            <p className="font-semibold text-foreground text-sm">QR Code da Sacola</p>
            <p className="text-xs text-muted-foreground">Escaneie ou digite o código</p>
          </div>
          <QrCode size={18} className="ml-auto text-muted-foreground" />
        </div>

        {step === 'qrcode' && (
          <form onSubmit={handleQrCodeSubmit} className="space-y-3">
            <input
              type="text"
              placeholder="BAG-00001:2026-05-13:checksum"
              value={qrCode}
              onChange={(e) => setQrCode(e.target.value)}
              disabled={isBuscando}
              autoFocus
              className={inputClass}
            />
            {error && (
              <div className="px-3 py-2.5 bg-destructive/10 border border-destructive/20 rounded-md">
                <p className="text-destructive text-sm">{error}</p>
              </div>
            )}
            <button
              type="submit"
              disabled={isBuscando}
              className={cn(
                'w-full h-10 rounded-md bg-primary text-primary-foreground font-medium text-sm',
                'hover:bg-primary/90 transition-colors disabled:opacity-50',
                'flex items-center justify-center gap-2'
              )}
            >
              {isBuscando ? <><Loader2 size={16} className="animate-spin" /> Buscando...</> : 'Continuar'}
            </button>
          </form>
        )}

        {step !== 'qrcode' && (
          <p className="text-sm text-foreground font-mono bg-secondary px-3 py-2 rounded-lg truncate">{qrCode}</p>
        )}
      </div>

      {/* Step 2 — Confirmar devolução */}
      {step === 'confirmar' && sacola && (
        <div className="bg-card border border-primary rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">2</div>
            <div>
              <p className="font-semibold text-foreground text-sm">Confirmar Devolução</p>
              <p className="text-xs text-muted-foreground">Verifique os dados antes de confirmar</p>
            </div>
            <RotateCcw size={18} className="ml-auto text-muted-foreground" />
          </div>

          {/* Informações da sacola */}
          <div className="bg-secondary rounded-xl p-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Sacola</span>
              <span className="font-medium text-foreground">{sacola.id}</span>
            </div>
            {sacola.cliente && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Cliente</span>
                <span className="font-medium text-foreground">{sacola.cliente.nome}</span>
              </div>
            )}
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Utilizações</span>
              <span className="font-medium text-foreground">{sacola.utilizacoes} / 40</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Dias de uso</span>
              <span className="font-medium text-foreground">{sacola.dias_de_uso}</span>
            </div>
            <div className="flex justify-between text-sm items-center">
              <span className="text-muted-foreground">Estado</span>
              <span className={cn('text-xs font-semibold px-2 py-0.5 rounded-full border',
                estadoConfig[sacola.estado]?.bg,
                estadoConfig[sacola.estado]?.color
              )}>
                {estadoConfig[sacola.estado]?.label ?? sacola.estado}
              </span>
            </div>
          </div>

          {/* Desconto a receber */}
          <div className={cn(
            'px-4 py-3 rounded-xl border flex items-center gap-3',
            sacola.descontos.devolucao > 0
              ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
              : 'bg-secondary border-border'
          )}>
            {sacola.descontos.devolucao > 0 ? (
              <>
                <CheckCircle size={18} className="text-green-600 dark:text-green-400 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-green-700 dark:text-green-300">
                    Desconto de devolução: {formatMoney(sacola.descontos.devolucao)}
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-400">Aplicar no próximo cupom do cliente</p>
                </div>
              </>
            ) : (
              <>
                <AlertTriangle size={18} className="text-muted-foreground flex-shrink-0" />
                <p className="text-sm text-muted-foreground">Sacola expirada — sem desconto de devolução</p>
              </>
            )}
          </div>

          {error && (
            <div className="px-3 py-2.5 bg-destructive/10 border border-destructive/20 rounded-md">
              <p className="text-destructive text-sm">{error}</p>
            </div>
          )}

          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => { setStep('qrcode'); setError(null); setSacola(null); }}
              className="h-10 px-4 rounded-md bg-secondary text-secondary-foreground text-sm font-medium hover:bg-secondary/80 transition-colors"
            >
              Voltar
            </button>
            <button
              onClick={handleDevolver}
              disabled={isLoading}
              className={cn(
                'flex-1 h-10 rounded-md bg-primary text-primary-foreground font-medium text-sm',
                'hover:bg-primary/90 transition-colors disabled:opacity-50',
                'flex items-center justify-center gap-2'
              )}
            >
              {isLoading ? <><Loader2 size={16} className="animate-spin" /> Processando...</> : 'Confirmar Devolução'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}