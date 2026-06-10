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
  return request(`/api/sacolas/verificar-qr?qr_code=${encodeURIComponent(qrCode)}`);
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