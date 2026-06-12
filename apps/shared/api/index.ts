/**
 * @bagplus/shared - API
 * Funções de chamada à API real do Bag+
 */

import type { LoginResponse, Sacola, Cliente, SuccessResponse } from '../types/index';

// ============================================
// CONSTANTES INTERNAS
// ============================================

export const TOKEN_KEY = 'bagplus_token';
export const USER_KEY = 'bagplus_user';

// ============================================
// CONFIGURAÇÃO BASE
// ============================================

const getBaseUrl = (): string => {
  if (typeof window !== 'undefined') {
    const hostname = window.location.hostname;
    if (hostname === 'localhost' || hostname === '127.0.0.1') {
      return 'http://localhost:8000';
    }
    if (hostname.includes('staging')) {
      return 'https://staging.bagplus.com.br';
    }
  }
  return 'https://api.bagplus.com.br';
};

const getToken = (): string | null => {
  return sessionStorage.getItem(TOKEN_KEY);
};

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(`${getBaseUrl()}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erro desconhecido' }));
    throw new Error(error.detail || `Erro ${response.status}`);
  }

  return response.json();
}

// ============================================
// AUTENTICAÇÃO
// ============================================

export async function login(
  username: string,
  password: string,
  terminal?: string
): Promise<LoginResponse> {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);
  if (terminal) params.append('terminal', terminal);

  const response = await fetch(`${getBaseUrl()}/api/auth/login?${params.toString()}`, {
    method: 'POST',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Credenciais inválidas' }));
    throw new Error(error.detail || 'Erro ao fazer login');
  }

  return response.json();
}

export async function getMe() {
  return request('/api/auth/me');
}

// ============================================
// CLIENTES
// ============================================

export async function buscarCliente(cpf: string): Promise<Cliente> {
  const data = await request<{ existe: boolean; cliente: Cliente }>(`/api/clientes/${cpf}/validar`);
  if (!data.existe) throw new Error('Cliente não encontrado');
  return data.cliente;
}

export async function buscarClientePorNome(nome: string): Promise<Cliente[]> {
  const data = await request<{ clientes: Cliente[] }>(
    `/api/clientes/buscar?nome=${encodeURIComponent(nome)}`
  );
  return data.clientes;
}

export async function cadastrarCliente(
  cpf: string,
  nome: string,
  telefone?: string
): Promise<Cliente> {
  const params = new URLSearchParams();
  params.append('cpf', cpf);
  params.append('nome', nome);
  if (telefone) params.append('telefone', telefone);

  const token = getToken();
  const response = await fetch(`${getBaseUrl()}/api/clientes/?${params.toString()}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Erro ao cadastrar cliente' }));
    throw new Error(error.detail || 'Erro ao cadastrar cliente');
  }

  const data = await response.json();
  return data.cliente || data;
}

export async function editarCliente(
  cpf: string,
  dados: { nome?: string; telefone?: string }
): Promise<Cliente> {
  const params = new URLSearchParams();
  if (dados.nome) params.append('nome', dados.nome);
  if (dados.telefone !== undefined) params.append('telefone', dados.telefone);

  const data = await request<{ sucesso: boolean; cliente: Cliente }>(
    `/api/clientes/${cpf}?${params.toString()}`,
    { method: 'PUT' }
  );
  return data.cliente;
}

export async function verificarCpf(cpf: string): Promise<{ existe: boolean; ativo: boolean }> {
  return request(`/api/clientes/validar-cpf?cpf=${cpf}`, {
    method: 'POST',
  });
}

export interface EstatisticasCliente {
  cliente: { cpf: string; nome: string };
  estatisticas: {
    total_gasto: number;
    valor_medio_compra: number;
    total_usos: number;
    sacolas_ativas: number;
  };
}

export async function estatisticasCliente(cpf: string): Promise<EstatisticasCliente> {
  return request(`/api/clientes/${cpf}/estatisticas`);
}

export interface TimelineEvento {
  tipo: string;
  data: string;
  descricao: string;
  valor?: number;
  gravidade?: string;
}

export interface HistoricoCompletoCliente {
  cliente: {
    cpf: string;
    nome: string;
    data_cadastro: string;
    status_beneficios: string;
    motivo_suspensao: string | null;
    data_suspensao: string | null;
  };
  resumo_compras: {
    total_gasto: number;
    valor_medio_compra: number;
    total_usos: number;
    primeira_compra: string | null;
    ultima_compra: string | null;
  };
  sacolas: {
    total_sacolas_vinculadas: number;
    ativas: number;
    devolvidas: number;
    lista_ativas: string[];
    lista_devolvidas: string[];
  };
  alertas: {
    total: number;
    lista: any[];
  };
  timeline: TimelineEvento[];
}

export async function historicoCompletoCliente(cpf: string): Promise<HistoricoCompletoCliente> {
  return request(`/api/clientes/${cpf}/historico-completo`);
}

// ============================================
// AUDITORIA (CAIXA)
// ============================================

export interface UltimaAcao {
  acao: string;
  timestamp: string;
  sacola_id?: string | null;
  cliente_nome?: string | null;
  valor_compra?: number | null;
  desconto_concedido?: number | null;
}

export interface MeuTurno {
  data: string;
  usuario: { id: number; nome: string; username: string };
  resumo: {
    ativacoes: number;
    usos_registrados: number;
    devolucoes: number;
    total_operacoes: number;
  };
  ultimas_acoes: UltimaAcao[];
}

export async function meuTurno(): Promise<MeuTurno> {
  return request('/api/auditoria/meu-turno');
}

// ============================================
// SACOLAS
// ============================================

export async function buscarSacola(sacolaId: string): Promise<Sacola> {
  return request(`/api/sacolas/${sacolaId}`);
}

export async function verificarQrCode(qrCode: string): Promise<{
  valido: boolean;
  sacola_id?: string;
  data_criacao?: string;
  status?: string;
  erro?: string;
}> {
  return request(`/api/sacolas/verificar-qr?qr_code=${encodeURIComponent(qrCode)}`, {
    method: 'POST',
  });
}

export async function ativarSacola(
  qrCode: string,
  cpfCliente: string
): Promise<
  SuccessResponse & {
    sacola: { id: string; status: string };
    cliente: { cpf: string; nome: string };
  }
> {
  return request(
    `/api/sacolas/ativar?qr_code=${encodeURIComponent(qrCode)}&cpf_cliente=${cpfCliente}`,
    { method: 'POST' }
  );
}

export async function registrarUso(
  qrCode: string,
  valorCompra: string
): Promise<{
  sucesso: boolean;
  mensagem: string;
  sacola: { id: string; utilizacoes: number; usos_restantes: number };
  valor_compra: number;
  desconto_fidelidade: {
    desconto_atual: number;
    proximo_marco: number | null;
  };
}> {
  return request(
    `/api/sacolas/registrar-uso?qr_code=${encodeURIComponent(qrCode)}&valor_compra=${encodeURIComponent(valorCompra)}`,
    { method: 'POST' }
  );
}

export async function devolverSacola(sacolaId: string): Promise<{
  sucesso: boolean;
  mensagem: string;
  sacola: { id: string; utilizacoes: number; dias_de_uso: number; estado: string };
  desconto_concedido: number;
}> {
  return request(`/api/sacolas/devolver?sacola_id=${sacolaId}`, {
    method: 'POST',
  });
}

export interface HistoricoUsoSacola {
  sacola_id: string;
  total_usos: number;
  total_gasto: number;
  valor_medio: number;
  historico: { data_uso: string; valor_compra: number }[];
}

export async function historicoSacola(sacolaId: string): Promise<HistoricoUsoSacola> {
  return request(`/api/sacolas/${sacolaId}/historico`);
}