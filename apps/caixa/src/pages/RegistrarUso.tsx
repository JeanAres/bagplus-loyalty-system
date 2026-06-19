import { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { registrarUso, buscarSacola } from '@bagplus/shared/api';
import { formatMoney, parseMoney } from '@bagplus/shared/utils';
import type { Sacola } from '@bagplus/shared/types';
import { ShoppingBag, CheckCircle, Loader2, QrCode } from 'lucide-react';
import { cn } from '../lib/utils';

type Step = 'qrcode' | 'valor' | 'success';

const estadoConfig = {
  verde: { label: 'Verde', color: 'text-green-600 dark:text-green-400', bg: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' },
  amarelo: { label: 'Amarelo', color: 'text-yellow-600 dark:text-yellow-400', bg: 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800' },
  vermelho: { label: 'Vermelho', color: 'text-red-600 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800' },
  expirado: { label: 'Expirado', color: 'text-destructive', bg: 'bg-destructive/10 border-destructive/20' },
};

interface ResultadoUso {
  mensagem: string;
  sacola: { id: string; utilizacoes: number; usos_restantes: number };
  valor_compra: number;
  desconto_fidelidade: { desconto_atual: number; proximo_marco: number | null };
}

function formatarValorInput(input: string): string {
  const digits = input.replace(/\D/g, '');
  if (!digits) return '';
  const number = parseInt(digits, 10) / 100;
  return number.toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export default function RegistrarUso() {
  const location = useLocation();
  const navigate = useNavigate();
  const [step, setStep] = useState<Step>('qrcode');
  const [sugerirDevolucao, setSugerirDevolucao] = useState(false);
  const [qrCode, setQrCode] = useState('');
  const [valor, setValor] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isBuscando, setIsBuscando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sacola, setSacola] = useState<Sacola | null>(null);
  const [resultado, setResultado] = useState<ResultadoUso | null>(null);

  // Pré-preenche QR Code vindo da Leitura Rápida (Home) e busca a sacola automaticamente
  useEffect(() => {
    const state = location.state as { qrCode?: string; sugerirDevolucao?: boolean } | null;
    const qrFromState = state?.qrCode;
    if (qrFromState) {
      const partes = qrFromState.trim().split(':');
      if (partes.length === 3 && partes[0].startsWith('BAG-')) {
        setQrCode(qrFromState);
        setSugerirDevolucao(!!state?.sugerirDevolucao);
        setIsBuscando(true);
        buscarSacola(partes[0])
          .then((info) => {
            setSacola(info);
            setStep('valor');
          })
          .catch((err) => {
            setError(err instanceof Error ? err.message : 'Sacola não encontrada');
          })
          .finally(() => setIsBuscando(false));
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
      setSacola(info);
      setStep('valor');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Sacola não encontrada');
    } finally {
      setIsBuscando(false);
    }
  };

  const handleRegistrar = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const valorNum = parseMoney(valor);
    if (isNaN(valorNum) || valorNum < 15) {
      setError('Valor mínimo de compra: R$ 15,00');
      return;
    }

    setIsLoading(true);
    try {
      const res = await registrarUso(qrCode.trim(), valor);
      setResultado(res);
      setStep('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao registrar uso');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNovo = () => {
    setStep('qrcode');
    setQrCode('');
    setValor('');
    setSacola(null);
    setResultado(null);
    setError(null);
  };

  const inputClass = cn(
    'w-full h-10 px-3 rounded-md border bg-input text-foreground placeholder:text-muted-foreground',
    'focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent',
    'disabled:opacity-50 transition-colors text-sm'
  );

  if (step === 'success' && resultado) {
    const desconto = resultado.desconto_fidelidade.desconto_atual;
    const proximoMarco = resultado.desconto_fidelidade.proximo_marco;

    return (
      <div className="max-w-md mx-auto">
        <div className="bg-card border border-border rounded-2xl p-8 text-center">
          <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} className="text-green-600 dark:text-green-400" />
          </div>
          <h2 className="text-xl font-bold text-foreground mb-1">Uso registrado!</h2>
          <p className="text-muted-foreground text-sm mb-6">{resultado.mensagem}</p>

          <div className="bg-secondary rounded-xl p-4 text-left mb-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Sacola</span>
              <span className="font-medium text-foreground">{resultado.sacola.id}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Valor da compra</span>
              <span className="font-medium text-foreground">{formatMoney(resultado.valor_compra)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Usos restantes</span>
              <span className="font-medium text-foreground">{resultado.sacola.usos_restantes}</span>
            </div>
          </div>

          {desconto > 0 && (
            <div className="px-4 py-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-xl mb-4">
              <p className="text-sm text-green-700 dark:text-green-300 font-medium">
                🎉 Desconto de fidelidade disponível: {formatMoney(desconto)}
              </p>
            </div>
          )}

          {proximoMarco && (
            <p className="text-xs text-muted-foreground mb-6">
              Próximo desconto em {proximoMarco} usos
            </p>
          )}

          <button
            onClick={handleNovo}
            className="w-full h-10 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Registrar outro uso
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

      {/* Step 2 — Prévia + Valor */}
      {step === 'valor' && sacola && (
        <div className="bg-card border border-primary rounded-2xl p-6 shadow-sm space-y-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center text-sm font-bold">2</div>
            <div>
              <p className="font-semibold text-foreground text-sm">Confirmar e Registrar</p>
              <p className="text-xs text-muted-foreground">Verifique os dados e informe o valor</p>
            </div>
            <ShoppingBag size={18} className="ml-auto text-muted-foreground" />
          </div>

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

          {sugerirDevolucao && (
            <button
              type="button"
              onClick={() => navigate('/devolucao', { state: { qrCode } })}
              className="w-full text-left px-3 py-2.5 bg-secondary rounded-lg text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              Prefere devolver esta sacola em vez de registrar uso? <span className="text-primary font-medium">Ir para devolução</span>
            </button>
          )}

          <form onSubmit={handleRegistrar} className="space-y-3">
            <div className="space-y-1.5">
              <label className="text-sm font-medium text-foreground">Valor da compra</label>
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-sm">R$</span>
                <input
                  type="text"
                  inputMode="numeric"
                  placeholder="0,00"
                  value={valor}
                  onChange={(e) => setValor(formatarValorInput(e.target.value))}
                  disabled={isLoading}
                  autoFocus
                  className={cn(inputClass, 'pl-9')}
                />
              </div>
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
                type="submit"
                disabled={isLoading || !valor}
                className={cn(
                  'flex-1 h-10 rounded-md bg-primary text-primary-foreground font-medium text-sm',
                  'hover:bg-primary/90 transition-colors disabled:opacity-50',
                  'flex items-center justify-center gap-2'
                )}
              >
                {isLoading ? <><Loader2 size={16} className="animate-spin" /> Registrando...</> : 'Registrar Uso'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}