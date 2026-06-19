import { useState } from 'react';
import { cadastrarCliente, verificarCpf } from '@bagplus/shared/api';
import { formatCPF, cleanCPF, validateCPF } from '@bagplus/shared/utils';
import { UserPlus, CheckCircle, Loader2 } from 'lucide-react';
import { cn } from '../lib/utils';

type Step = 'form' | 'success';

export default function CadastrarCliente() {
  const [step, setStep] = useState<Step>('form');
  const [cpf, setCpf] = useState('');
  const [nome, setNome] = useState('');
  const [telefone, setTelefone] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [clienteCriado, setClienteCriado] = useState<{ cpf: string; nome: string } | null>(null);

  const handleCpfChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const raw = cleanCPF(e.target.value);
    if (raw.length <= 11) setCpf(raw);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!validateCPF(cpf)) {
      setError('CPF inválido. Verifique os dígitos.');
      return;
    }

    if (nome.trim().length < 3) {
      setError('Nome deve ter pelo menos 3 caracteres.');
      return;
    }

    setIsLoading(true);
    try {
      // Verifica se CPF já existe
      const verificacao = await verificarCpf(cpf);
      if (verificacao.existe) {
        setError('CPF já cadastrado no sistema.');
        return;
      }

      const cliente = await cadastrarCliente(cpf, nome.trim(), telefone.trim() || undefined);
      setClienteCriado({ cpf: cliente.cpf, nome: cliente.nome });
      setStep('success');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erro ao cadastrar cliente');
    } finally {
      setIsLoading(false);
    }
  };

  const handleNovoCadastro = () => {
    setCpf('');
    setNome('');
    setTelefone('');
    setError(null);
    setClienteCriado(null);
    setStep('form');
  };

  if (step === 'success' && clienteCriado) {
    return (
      <div className="max-w-md mx-auto">
        <div className="bg-card border border-border rounded-2xl p-8 text-center">
          <div className="w-16 h-16 bg-green-100 dark:bg-green-900/30 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle size={32} className="text-green-600 dark:text-green-400" />
          </div>
          <h2 className="text-xl font-bold text-foreground mb-1">Cliente cadastrado!</h2>
          <p className="text-muted-foreground text-sm mb-6">
            {clienteCriado.nome} foi cadastrado(a) com sucesso.
          </p>

          <div className="bg-secondary rounded-xl p-4 text-left mb-6 space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Nome</span>
              <span className="font-medium text-foreground">{clienteCriado.nome}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">CPF</span>
              <span className="font-medium text-foreground">{formatCPF(clienteCriado.cpf)}</span>
            </div>
          </div>

          <button
            onClick={handleNovoCadastro}
            className="w-full h-10 rounded-lg bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors"
          >
            Cadastrar outro cliente
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-md mx-auto">
      <div className="bg-card border border-border rounded-2xl p-8">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 bg-primary/10 rounded-xl flex items-center justify-center">
            <UserPlus size={20} className="text-primary" />
          </div>
          <div>
            <h2 className="font-semibold text-foreground">Novo Cliente</h2>
            <p className="text-xs text-muted-foreground">Preencha os dados para cadastrar</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">

          {/* CPF */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">
              CPF <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              inputMode="numeric"
              placeholder="000.000.000-00"
              value={formatCPF(cpf)}
              onChange={handleCpfChange}
              disabled={isLoading}
              className={cn(
                'w-full h-10 px-3 rounded-md border bg-input text-foreground placeholder:text-muted-foreground',
                'focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent',
                'disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm'
              )}
            />
          </div>

          {/* Nome */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">
              Nome completo <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              placeholder="Nome do cliente"
              value={nome}
              onChange={(e) => setNome(e.target.value)}
              disabled={isLoading}
              className={cn(
                'w-full h-10 px-3 rounded-md border bg-input text-foreground placeholder:text-muted-foreground',
                'focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent',
                'disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm'
              )}
            />
          </div>

          {/* Telefone */}
          <div className="space-y-1.5">
            <label className="text-sm font-medium text-foreground">
              Telefone <span className="text-muted-foreground text-xs">(opcional)</span>
            </label>
            <input
              type="tel"
              inputMode="numeric"
              placeholder="(00) 00000-0000"
              value={telefone}
              onChange={(e) => setTelefone(e.target.value)}
              disabled={isLoading}
              className={cn(
                'w-full h-10 px-3 rounded-md border bg-input text-foreground placeholder:text-muted-foreground',
                'focus:outline-none focus:ring-2 focus:ring-ring focus:border-transparent',
                'disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm'
              )}
            />
          </div>

          {/* Erro */}
          {error && (
            <div className="px-3 py-2.5 bg-destructive/10 border border-destructive/20 rounded-md">
              <p className="text-destructive text-sm">{error}</p>
            </div>
          )}

          {/* Botão */}
          <button
            type="submit"
            disabled={isLoading || cpf.length !== 11}
            className={cn(
              'w-full h-10 rounded-md bg-primary text-primary-foreground font-medium text-sm',
              'hover:bg-primary/90 transition-colors',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'flex items-center justify-center gap-2 mt-2'
            )}
          >
            {isLoading ? (
              <>
                <Loader2 size={16} className="animate-spin" />
                Cadastrando...
              </>
            ) : (
              'Cadastrar Cliente'
            )}
          </button>
        </form>
      </div>
    </div>
  );
}