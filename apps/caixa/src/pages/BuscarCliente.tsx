import { useState } from 'react';
import { buscarCliente, buscarClientePorNome, editarCliente } from '@bagplus/shared/api';
import { formatCPF, cleanCPF, validateCPF, formatDateTime, formatTelefone } from '@bagplus/shared/utils';
import type { Cliente } from '@bagplus/shared/types';
import { Search, User, ShoppingBag, Loader2, AlertCircle, CheckCircle, XCircle, Pencil, X, Check } from 'lucide-react';
import { cn } from '../lib/utils';

type BuscaTipo = 'cpf' | 'nome';

export default function BuscarCliente() {
  const [buscaTipo, setBuscaTipo] = useState<BuscaTipo>('cpf');
  const [termo, setTermo] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [cliente, setCliente] = useState<Cliente | null>(null);
  const [resultados, setResultados] = useState<Cliente[]>([]);

  // Edição
  const [editando, setEditando] = useState(false);
  const [editNome, setEditNome] = useState('');
  const [editTelefone, setEditTelefone] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const handleCpfChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = cleanCPF(e.target.value);
    if (raw.length <= 11) setTermo(raw);
  };

  const handleBuscar = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setCliente(null);
    setResultados([]);
    setEditando(false);

    if (!termo.trim()) {
      setError('Preencha o campo de busca');
      return;
    }

    if (buscaTipo === 'cpf' && !validateCPF(termo)) {
      setError('CPF inválido');
      return;
    }

    if (buscaTipo === 'nome' && termo.trim().length < 3) {
      setError('Digite pelo menos 3 caracteres para buscar por nome');
      return;
    }

    setIsLoading(true);
    try {
      if (buscaTipo === 'cpf') {
        const result = await buscarCliente(termo);
        setCliente(result);
      } else {
        const clientes = await buscarClientePorNome(termo.trim());
        setResultados(clientes);
        if (clientes.length === 0) setError('Nenhum cliente encontrado');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao buscar cliente');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSelecionarCliente = async (cpf: string) => {
    setIsLoading(true);
    setError(null);
    setEditando(false);
    try {
      const result = await buscarCliente(cpf);
      setCliente(result);
      setResultados([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao buscar cliente');
    } finally {
      setIsLoading(false);
    }
  };

  const handleLimpar = () => {
    setTermo('');
    setCliente(null);
    setResultados([]);
    setError(null);
    setEditando(false);
  };

  const handleIniciarEdicao = () => {
    if (!cliente) return;
    setEditNome(cliente.nome);
    setEditTelefone(cliente.telefone || '');
    setEditError(null);
    setEditando(true);
  };

  const handleCancelarEdicao = () => {
    setEditando(false);
    setEditError(null);
  };

  const handleSalvarEdicao = async () => {
    if (!cliente) return;
    setEditError(null);
    setIsSaving(true);
    try {
      const atualizado = await editarCliente(cliente.cpf, {
        nome: editNome,
        telefone: editTelefone,
      });
      setCliente({ ...cliente, ...atualizado });
      setEditando(false);
    } catch (err) {
      setEditError(err instanceof Error ? err.message : 'Erro ao salvar');
    } finally {
      setIsSaving(false);
    }
  };

  const statusColor = {
    ativo: 'text-green-600 dark:text-green-400',
    suspenso: 'text-yellow-600 dark:text-yellow-400',
    bloqueado: 'text-destructive',
  };

  const StatusIcon = {
    ativo: CheckCircle,
    suspenso: AlertCircle,
    bloqueado: XCircle,
  };

  const inputClass = cn(
    'w-full h-10 px-3 rounded-md border bg-input text-foreground placeholder:text-muted-foreground',
    'focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent',
    'disabled:opacity-50 transition-colors text-sm'
  );

  return (
    <div className="max-w-2xl mx-auto space-y-6">

      {/* Formulário de busca */}
      <div className="bg-card border border-border rounded-2xl p-6">
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center">
            <Search size={20} className="text-primary" />
          </div>
          <div>
            <h2 className="font-semibold text-foreground">Buscar Cliente</h2>
            <p className="text-xs text-muted-foreground">Busque por CPF ou nome</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 mb-4">
          {(['cpf', 'nome'] as BuscaTipo[]).map((tipo) => (
            <button
              key={tipo}
              onClick={() => { setBuscaTipo(tipo); setTermo(''); setError(null); }}
              className={cn(
                'px-4 py-1.5 rounded-lg text-sm font-medium transition-colors',
                buscaTipo === tipo
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-muted-foreground hover:text-foreground'
              )}
            >
              {tipo === 'cpf' ? 'Por CPF' : 'Por Nome'}
            </button>
          ))}
        </div>

        <form onSubmit={handleBuscar} className="space-y-3">
          <input
            type="text"
            inputMode={buscaTipo === 'cpf' ? 'numeric' : 'text'}
            placeholder={buscaTipo === 'cpf' ? '000.000.000-00' : 'Nome do cliente'}
            value={buscaTipo === 'cpf' ? formatCPF(termo) : termo}
            onChange={buscaTipo === 'cpf' ? handleCpfChange : (e) => setTermo(e.target.value)}
            disabled={isLoading}
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
              disabled={isLoading}
              className={cn(
                'flex-1 h-10 rounded-md bg-primary text-primary-foreground font-medium text-sm',
                'hover:bg-primary/90 transition-colors disabled:opacity-50',
                'flex items-center justify-center gap-2'
              )}
            >
              {isLoading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
              {isLoading ? 'Buscando...' : 'Buscar'}
            </button>
            {(cliente || resultados.length > 0) && (
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

      {/* Lista de resultados (busca por nome) */}
      {resultados.length > 0 && (
        <div className="bg-card border border-border rounded-2xl overflow-hidden">
          <div className="px-6 py-3 border-b border-border">
            <p className="text-sm font-medium text-foreground">{resultados.length} cliente(s) encontrado(s)</p>
          </div>
          <div className="divide-y divide-border">
            {resultados.map((c) => (
              <button
                key={c.cpf}
                onClick={() => handleSelecionarCliente(c.cpf)}
                className="w-full flex items-center justify-between px-6 py-3 hover:bg-secondary transition-colors text-left"
              >
                <div>
                  <p className="font-medium text-foreground text-sm">{c.nome}</p>
                  <p className="text-xs text-muted-foreground">{formatCPF(c.cpf)}</p>
                </div>
                <span className={cn('text-xs font-medium', statusColor[c.status_beneficios])}>
                  {c.status_beneficios}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Detalhes do cliente */}
      {cliente && (
        <div className="bg-card border border-border rounded-2xl overflow-hidden">

          {/* Header */}
          <div className="px-6 py-4 border-b border-border flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                <User size={18} className="text-primary" />
              </div>
              <div>
                <p className="font-semibold text-foreground">{cliente.nome}</p>
                <p className="text-xs text-muted-foreground">{formatCPF(cliente.cpf)}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className={cn('flex items-center gap-1.5 text-sm font-medium', statusColor[cliente.status_beneficios])}>
                {(() => {
                  const Icon = StatusIcon[cliente.status_beneficios];
                  return <Icon size={16} />;
                })()}
                {cliente.status_beneficios}
              </div>
              {!editando && (
                <button
                  onClick={handleIniciarEdicao}
                  className="p-1.5 rounded-lg hover:bg-secondary transition-colors text-muted-foreground hover:text-foreground"
                  title="Editar dados"
                >
                  <Pencil size={16} />
                </button>
              )}
            </div>
          </div>

          {/* Dados / Formulário de edição */}
          <div className="px-6 py-4 space-y-3">
            {editando ? (
              <>
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-muted-foreground">Nome completo</label>
                    <input
                      type="text"
                      value={editNome}
                      onChange={(e) => setEditNome(e.target.value)}
                      disabled={isSaving}
                      className={inputClass}
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium text-muted-foreground">Telefone</label>
                    <input
                      type="text"
                      inputMode="numeric"
                      value={editTelefone}
                      onChange={(e) => setEditTelefone(e.target.value.replace(/\D/g, ''))}
                      disabled={isSaving}
                      placeholder="(00) 00000-0000"
                      className={inputClass}
                    />
                  </div>
                </div>

                {editError && (
                  <div className="px-3 py-2 bg-destructive/10 border border-destructive/20 rounded-md">
                    <p className="text-destructive text-xs">{editError}</p>
                  </div>
                )}

                <div className="flex gap-2 pt-1">
                  <button
                    onClick={handleSalvarEdicao}
                    disabled={isSaving}
                    className={cn(
                      'flex-1 h-9 rounded-md bg-primary text-primary-foreground text-sm font-medium',
                      'hover:bg-primary/90 transition-colors disabled:opacity-50',
                      'flex items-center justify-center gap-2'
                    )}
                  >
                    {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
                    {isSaving ? 'Salvando...' : 'Salvar'}
                  </button>
                  <button
                    onClick={handleCancelarEdicao}
                    disabled={isSaving}
                    className="h-9 px-4 rounded-md bg-secondary text-secondary-foreground text-sm font-medium hover:bg-secondary/80 transition-colors flex items-center gap-1.5"
                  >
                    <X size={14} />
                    Cancelar
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-secondary rounded-xl p-3">
                    <p className="text-xs text-muted-foreground mb-1">Telefone</p>
                    <p className="text-sm font-medium text-foreground">{formatTelefone(cliente.telefone || '')}</p>
                  </div>
                  <div className="bg-secondary rounded-xl p-3">
                    <p className="text-xs text-muted-foreground mb-1">Cadastro</p>
                    <p className="text-sm font-medium text-foreground">{formatDateTime(cliente.data_cadastro)}</p>
                  </div>
                </div>

                {cliente.status_beneficios !== 'ativo' && cliente.motivo_suspensao && (
                  <div className="px-3 py-2.5 bg-destructive/10 border border-destructive/20 rounded-lg">
                    <p className="text-xs text-destructive font-medium">Motivo: {cliente.motivo_suspensao}</p>
                  </div>
                )}

                <div className="flex items-center justify-between py-2 border-t border-border">
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <ShoppingBag size={16} />
                    Sacolas ativas
                  </div>
                  <span className="text-sm font-semibold text-foreground">
                    {(cliente as any).sacolas_ativas ?? '—'}
                  </span>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}