import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { ativarSacola, buscarCliente } from '@bagplus/shared/api';
import { formatCPF, cleanCPF, validateCPF } from '@bagplus/shared/utils';
import { QrCode, CheckCircle, Loader2, User } from 'lucide-react';
import { cn } from '../lib/utils';

type Step = 'qrcode' | 'cliente' | 'success';

interface ResultadoAtivacao {
  sacola: { id: string; status: string };
  cliente: { cpf: string; nome: string };
}

export default function AtivarSacola() {
  const location = useLocation();
  const [step, setStep] = useState<Step>('qrcode');
  const [qrCode, setQrCode] = useState('');
  const [cpf, setCpf] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clienteNome, setClienteNome] = useState('');
  const [resultado, setResultado] = useState<ResultadoAtivacao | null>(null);

  // Pré-preenche QR Code vindo da Leitura Rápida (Home) e avança automaticamente
  useEffect(() => {
    const qrFromState = (location.state as { qrCode?: string } | null)?.qrCode;
    if (qrFromState) {
      const partes = qrFromState.trim().split(':');
      if (partes.length === 3 && partes[0].startsWith('BAG-')) {
        setQrCode(qrFromState);
        setStep('cliente');
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

    setStep('cliente');
  };

  const handleCpfChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = cleanCPF(e.target.value);
    if (raw.length <= 11) setCpf(raw);
  };

  const handleCpfBlur = async () => {
    if (cpf.length === 11 && validateCPF(cpf)) {
      try {
        const cliente = await buscarCliente(cpf);
        setClienteNome(cliente.nome);
        setError(null);
      } catch {
        setClienteNome('');
      }
    }
  };

  const handleAtivar = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateCPF(cpf)) {
      setError('CPF inválido');
      return;
    }

    setIsLoading(true);
    try {
      const res = await ativarSacola(qrCode.trim(), cpf);
      setResultado(res);
      setStep('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao ativar sacola');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNova = () => {
    setStep('qrcode');
    setQrCode('');
    setCpf('');
    setClienteNome('');
    setError(null);
    setResultado(null);
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
          <h2 className="text-xl font-bold text-foreground mb-1">Sacola ativada!</h2>
          <p className="text-muted-foreground text-sm mb-6">
            Sacola vinculada com sucesso ao cliente.
          </p>

          <div className="bg-secondary rounded-xl p-4 text-left mb-6 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Sacola</span>
              <span className="font-medium text-foreground">{resultado.sacola.id}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Cliente</span>
              <span className="font-medium text-foreground">{resultado.cliente.nome}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">CPF</span>
              <span className="font-medium text-foreground">{formatCPF(resultado.cliente.cpf)}</span>
            </div>
          </div>

          <button
            onClick={handleNova}
            className="w-full h-10 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Ativar outra sacola
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
              disabled={isLoading}
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
              className="w-full h-10 rounded-md bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 transition-colors"
            >
              Continuar
            </button>
          </form>
        )}

        {step !== 'qrcode' && (
          <p className="text-sm text-foreground font-mono bg-secondary px-3 py-2 rounded-lg truncate">{qrCode}</p>
        )}
      </div>

      {/* Step 2 — CPF do cliente */}
      <div className={cn(
        'bg-card border rounded-2xl p-6 transition-all',
        step === 'cliente' ? 'border-primary shadow-sm' : 'border-border opacity-60'
      )}>
        <div className="flex items-center gap-3 mb-5">
          <div className={cn(
            'w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold',
            step === 'cliente' ? 'bg-primary text-primary-foreground' : 'bg-secondary text-muted-foreground'
          )}>2</div>
          <div>
            <p className="font-semibold text-foreground text-sm">CPF do Cliente</p>
            <p className="text-xs text-muted-foreground">Informe o CPF para vincular</p>
          </div>
          <User size={18} className="ml-auto text-muted-foreground" />
        </div>

        {step === 'cliente' && (
          <form onSubmit={handleAtivar} className="space-y-3">
            <input
              type="text"
              inputMode="numeric"
              placeholder="000.000.000-00"
              value={formatCPF(cpf)}
              onChange={handleCpfChange}
              onBlur={handleCpfBlur}
              disabled={isLoading}
              autoFocus
              className={inputClass}
            />

            {clienteNome && (
              <div className="flex items-center gap-2 px-3 py-2 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-md">
                <CheckCircle size={14} className="text-green-600 dark:text-green-400" />
                <p className="text-sm text-green-700 dark:text-green-300 font-medium">{clienteNome}</p>
              </div>
            )}

            {error && (
              <div className="px-3 py-2.5 bg-destructive/10 border border-destructive/20 rounded-md">
                <p className="text-destructive text-sm">{error}</p>
              </div>
            )}

            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => { setStep('qrcode'); setError(null); }}
                className="h-10 px-4 rounded-md bg-secondary text-secondary-foreground text-sm font-medium hover:bg-secondary/80 transition-colors"
              >
                Voltar
              </button>
              <button
                type="submit"
                disabled={isLoading || cpf.length !== 11}
                className={cn(
                  'flex-1 h-10 rounded-md bg-primary text-primary-foreground font-medium text-sm',
                  'hover:bg-primary/90 transition-colors disabled:opacity-50',
                  'flex items-center justify-center gap-2'
                )}
              >
                {isLoading ? <><Loader2 size={16} className="animate-spin" /> Ativando...</> : 'Ativar Sacola'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}