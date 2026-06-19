import { useState } from 'react';
import { historicoSacola } from '@bagplus/shared/api';
import { formatMoney, formatDateTime } from '@bagplus/shared/utils';
import type { HistoricoUsoSacola } from '@bagplus/shared/api';
import { History, ShoppingBag, Loader2, Receipt } from 'lucide-react';
import { cn } from '../lib/utils';

export default function Historico() {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [resultado, setResultado] = useState<HistoricoUsoSacola | null>(null);

  const extrairSacolaId = (valor: string): string | null => {
    const trimmed = valor.trim();
    if (!trimmed) return null;

    // QR Code completo: BAG-00001:2026-05-13:checksum
    if (trimmed.includes(':')) {
      const partes = trimmed.split(':');
      if (partes[0].startsWith('BAG-')) return partes[0];
      return null;
    }

    // Apenas o ID: BAG-00001
    if (trimmed.toUpperCase().startsWith('BAG-')) return trimmed.toUpperCase();

    return null;
  };

  const handleBuscar = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResultado(null);

    const sacolaId = extrairSacolaId(input);
    if (!sacolaId) {
      setError('Informe um QR Code válido ou o ID da sacola (ex: BAG-00001)');
      return;
    }

    setIsLoading(true);
    try {
      const data = await historicoSacola(sacolaId);
      setResultado(data);
      if (data.historico.length === 0) {
        setError('Esta sacola ainda não possui histórico de usos');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao buscar histórico');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLimpar = () => {
    setInput('');
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
            <History size={20} className="text-primary" />
          </div>
          <div>
            <h2 className="font-semibold text-foreground">Histórico de Usos</h2>
            <p className="text-xs text-muted-foreground">Escaneie o QR Code ou digite o ID da sacola</p>
          </div>
        </div>

        <form onSubmit={handleBuscar} className="space-y-3">
          <input
            type="text"
            placeholder="BAG-00001 ou BAG-00001:2026-05-13:checksum"
            value={input}
            onChange={(e) => setInput(e.target.value)}
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
              disabled={isLoading || !input.trim()}
              className={cn(
                'flex-1 h-10 rounded-md bg-primary text-primary-foreground font-medium text-sm',
                'hover:bg-primary/90 transition-colors disabled:opacity-50',
                'flex items-center justify-center gap-2'
              )}
            >
              {isLoading ? <><Loader2 size={16} className="animate-spin" /> Buscando...</> : 'Buscar'}
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

      {/* Resumo */}
      {resultado && (
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="px-6 py-4 border-b border-border flex items-center gap-3">
            <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
              <ShoppingBag size={18} className="text-primary" />
            </div>
            <div>
              <p className="font-semibold text-foreground">{resultado.sacola_id}</p>
              <p className="text-xs text-muted-foreground">{resultado.total_usos} uso(s) registrado(s)</p>
            </div>
          </div>

          {resultado.total_usos > 0 && (
            <div className="px-6 py-4 grid grid-cols-2 gap-3 border-b border-border">
              <div className="bg-secondary rounded-xl p-3">
                <p className="text-xs text-muted-foreground mb-1">Total gasto</p>
                <p className="text-sm font-semibold text-foreground">{formatMoney(resultado.total_gasto)}</p>
              </div>
              <div className="bg-secondary rounded-xl p-3">
                <p className="text-xs text-muted-foreground mb-1">Valor médio</p>
                <p className="text-sm font-semibold text-foreground">{formatMoney(resultado.valor_medio)}</p>
              </div>
            </div>
          )}

          {/* Lista de usos */}
          {resultado.historico.length > 0 && (
            <div className="divide-y divide-border max-h-96 overflow-y-auto">
              {resultado.historico.map((uso, idx) => (
                <div key={idx} className="px-6 py-3 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-secondary rounded-full flex items-center justify-center flex-shrink-0">
                      <Receipt size={14} className="text-muted-foreground" />
                    </div>
                    <p className="text-sm text-foreground">{formatDateTime(uso.data_uso)}</p>
                  </div>
                  <span className="text-sm font-semibold text-foreground">{formatMoney(uso.valor_compra)}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}