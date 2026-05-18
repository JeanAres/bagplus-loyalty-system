// ============================================
// TIPOS BASE DA API
// ============================================

export type UserRole = 'admin' | 'gerente' | 'caixa';

export interface AuthUser {
  id: number;
  username: string;
  nome: string;
  role: UserRole;
  terminal?: string;
  entidade_id: number | null;
  unidade_id: number | null;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: AuthUser;
}

// ============================================
// SACOLAS
// ============================================

export type StatusSacola = 'estoque' | 'ativo' | 'devolvido';
export type EstadoSacola = 'verde' | 'amarelo' | 'vermelho' | 'expirado';

export interface Sacola {
  id: string;
  status: StatusSacola;
  utilizacoes: number;
  dias_de_uso: number;
  estado: EstadoSacola;
  cliente?: {
    cpf: string;
    nome: string;
  };
  descontos: {
    fidelidade: {
      desconto_atual: number;
      proximo_marco: number | null;
      proximo_desconto: number;
      usos_para_proximo: number;
    };
    devolucao: number;
  };
  ultima_utilizacao?: string;
}

// ============================================
// CLIENTES
// ============================================

export type StatusBeneficios = 'ativo' | 'suspenso' | 'bloqueado';

export interface Cliente {
  cpf: string;
  nome: string;
  telefone?: string;
  data_cadastro: string;
  status_beneficios: StatusBeneficios;
  motivo_suspensao?: string;
}

// ============================================
// MULTI-TENANCY
// ============================================

export interface Entidade {
  id: number;
  nome_comercial: string;
  cnpj: string;
  meta_desconto_percentual: number;
  meta_desconto_quantidade_usos: number;
  ativo: boolean;
}

export interface Unidade {
  id: number;
  entidade_id: number;
  nome: string;
  endereco?: string;
  cidade?: string;
  estado?: string;
  ativo: boolean;
}

// ============================================
// RESPOSTAS GENÉRICAS
// ============================================

export interface ApiError {
  detail: string;
}

export interface SuccessResponse {
  sucesso: boolean;
  mensagem: string;
}