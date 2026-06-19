import { useState } from 'react';
import { verificarQrCode } from '@bagplus/shared/api';
import { formatDate } from '@bagplus/shared/utils';
import { ScanLine, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { cn } from '../lib/utils';

const statusConfig: Record<string, { label: string; color: string }> = {
  estoque:   { label: 'Em estoque',    color: 'text-blue-600 dark:text-blue-400' },
  ativo:     { label: 'Ativo',         color: 'text-green-600 dark:text-green-400' },
  devolvido: { label: 'Devolvido',     color: 'text-yellow-600 dark:text-yellow-400' },
  expirado:  { label: 'Expirado',      color: 'text-destructive' },
};

interface ResultadoVerificacao {
  valido: boolean;
  sacola_id?: string;
  data_criacao?: string;
  status?: string;
  erro?: string;
}

export default function VerificarQr() {
  const [qrCode, setQrCode] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultado, setResultado] = useState<ResultadoVerificacao | null>(null);

  const handleVerificar = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResultado(null);

    if (!qrCode.trim()) {
      setError('Escaneie ou digite o QR Code');
      return;
    }

    setIsLoading(true);
    try {
      const res = await verificarQrCode(qrCode.trim());
      setResultado(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao verificar QR Code');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLimpar = () => {
    setQrCode('');
    setResultado(null);
    setError(null);
  };

  const inputClass = cn(
    'w-full h-10 px-3 rounded-md border bg-input text-foreground placeholder:text-muted-foreground',
    'focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent',
    'disabled:opacity-50 transition-colors text-sm'
  );

  return (
    <div className="max-w-md mx-auto space-y-4">

      {/* Formulário */}
      <div className="bg-card border border-border rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center">
            <ScanLine size={20} className="text-primary" />
          </div>
          <div>
            <h2 className="font-semibold text-foreground">Verificar QR Code</h2>
            <p className="text-xs text-muted-foreground">Consulta sem ativar a sacola</p>
          </div>
        </div>

        <form onSubmit={handleVerificar} className="space-y-3">
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

          <div className="flex gap-2">
            <button
              type="submit"
              disabled={isLoading || !qrCode.trim()}
              className={cn(
                'flex-1 h-10 rounded-md bg-primary text-primary-foreground font-medium text-sm',
                'hover:bg-primary/90 transition-colors disabled:opacity-50',
                'flex items-center justify-center gap-2'
              )}
            >
              {isLoading ? <><Loader2 size={16} className="animate-spin" /> Verificando...</> : 'Verificar'}
            </button>
            {resultado && (
              <button
                type="button"
                onClick={handleLimpar}
                className="h-10 px-4 rounded-md bg-secondary text-secondary-foreground text-sm font-medium hover:bg-secondary/80 transition-colors"
              >
                Limpar
              </button>
            )}
          </div>
        </form>
      </div>

      {/* Resultado */}
      {resultado && (
        <div className={cn(
          'bg-card border rounded-2xl p-6 space-y-4',
          resultado.valido ? 'border-green-200 dark:border-green-800' : 'border-destructive/30'
        )}>
          <div className="flex items-center gap-3">
            {resultado.valido ? (
              <CheckCircle size={22} className="text-green-600 dark:text-green-400 flex-shrink-0" />
            ) : (
              <XCircle size={22} className="text-destructive flex-shrink-0" />
            )}
            <p className={cn('font-semibold text-base', resultado.valido ? 'text-green-700 dark:text-green-300' : 'text-destructive')}>
              {resultado.valido ? 'QR Code válido' : 'QR Code inválido'}
            </p>
          </div>

          {resultado.valido ? (
            <div className="bg-secondary rounded-xl p-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Sacola</span>
                <span className="font-medium text-foreground">{resultado.sacola_id}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">Data de criação</span>
                <span className="font-medium text-foreground">{formatDate(resultado.data_criacao || '')}</span>
              </div>
              <div className="flex justify-between text-sm items-center">
                <span className="text-muted-foreground">Status</span>
                <span className={cn('text-sm font-semibold', statusConfig[resultado.status || '']?.color ?? 'text-foreground')}>
                  {statusConfig[resultado.status || '']?.label ?? resultado.status}
                </span>
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">{resultado.erro}</p>
          )}
        </div>
      )}
    </div>
  );
}