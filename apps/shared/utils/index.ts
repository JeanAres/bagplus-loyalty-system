/**
 * @bagplus/shared - Utils
 * Funções utilitárias compartilhadas entre os apps
 */

// ============================================
// CPF
// ============================================

export function formatCPF(cpf: string): string {
  const digits = cpf.replace(/\D/g, '');
  return digits.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
}

export function cleanCPF(cpf: string): string {
  return cpf.replace(/\D/g, '');
}

export function validateCPF(cpf: string): boolean {
  const digits = cleanCPF(cpf);
  if (digits.length !== 11) return false;
  if (/^(\d)\1+$/.test(digits)) return false;

  let sum = 0;
  for (let i = 0; i < 9; i++) sum += parseInt(digits[i]) * (10 - i);
  let remainder = (sum * 10) % 11;
  if (remainder === 10 || remainder === 11) remainder = 0;
  if (remainder !== parseInt(digits[9])) return false;

  sum = 0;
  for (let i = 0; i < 10; i++) sum += parseInt(digits[i]) * (11 - i);
  remainder = (sum * 10) % 11;
  if (remainder === 10 || remainder === 11) remainder = 0;
  return remainder === parseInt(digits[10]);
}

// ============================================
// DINHEIRO
// ============================================

export function formatMoney(value: number): string {
  return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

export function parseMoney(value: string): number {
  return parseFloat(value.replace(',', '.'));
}

// ============================================
// TELEFONE
// ============================================

export function formatTelefone(tel: string): string {
  if (!tel) return '—';
  const digits = tel.replace(/\D/g, '');
  if (digits.length === 11) {
    return digits.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
  }
  if (digits.length === 10) {
    return digits.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
  }
  return tel;
}

// ============================================
// DATA
// ============================================

export function formatDate(dateStr: string): string {
  if (!dateStr) return '—';
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return '—';
  return date.toLocaleDateString('pt-BR');
}

export function formatDateTime(dateStr: string): string {
  if (!dateStr) return '—';
  const date = new Date(dateStr);
  if (isNaN(date.getTime())) return '—';
  return date.toLocaleString('pt-BR');
}

// ============================================
// QR CODE
// ============================================

export function parseQrCode(qrCode: string): {
  valido: boolean;
  sacolaId?: string;
  dataCriacao?: string;
  checksum?: string;
} {
  const parts = qrCode.trim().split(':');
  if (parts.length !== 3) return { valido: false };
  const [sacolaId, dataCriacao, checksum] = parts;
  if (!sacolaId.startsWith('BAG-')) return { valido: false };
  return { valido: true, sacolaId, dataCriacao, checksum };
}