"""
Sistema de logging de eventos de segurança estruturado

Registra eventos críticos de segurança em formato JSON para análise
e detecção de ataques. Logs são escritos em tempo real.

Os logs são separados por ambiente (local, staging, production) para
evitar mistura de dados de diferentes ambientes.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


# Configurar diretório de logs
# Logs ficam em: services/backend/logs/
import os
BASE_DIR = Path(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Detectar ambiente atual
ENV = os.getenv("ENVIRONMENT", "local")  # local, staging, production

# Arquivo de logs de segurança por ambiente
SECURITY_LOG_FILE = LOG_DIR / f"security_{ENV}.log"


class SecurityLogger:
    """
    Logger especializado para eventos de segurança.
    
    Registra eventos em formato JSON estruturado para fácil análise.
    Cada evento é uma linha JSON completa (JSONL format).
    
    Logs são separados por ambiente usando a variável ENVIRONMENT:
    - local: logs/security_local.log (padrão)
    - staging: logs/security_staging.log
    - production: logs/security_production.log
    """
    
    def __init__(self):
        """Inicializa o logger de segurança."""
        self.logger = logging.getLogger("bagplus.security")
        self.logger.setLevel(logging.INFO)
        
        # Evitar duplicação de handlers
        if not self.logger.handlers:
            # Handler para arquivo
            file_handler = logging.FileHandler(SECURITY_LOG_FILE, encoding='utf-8')
            file_handler.setLevel(logging.INFO)
            
            # Formato: apenas a mensagem (já será JSON)
            formatter = logging.Formatter('%(message)s')
            file_handler.setFormatter(formatter)
            
            self.logger.addHandler(file_handler)
    
    def _log_event(self, event_type: str, details: Dict[str, Any], level: str = "INFO"):
        """
        Registra um evento de segurança.
        
        Args:
            event_type: Tipo do evento (login_failed, rate_limit, etc)
            details: Detalhes específicos do evento
            level: Nível de severidade (INFO, WARNING, ERROR)
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "event_type": event_type,
            "environment": ENV,  # Adiciona ambiente ao log
            **details  # Adiciona todos os detalhes do evento
        }
        
        # Escrever JSON em uma linha
        json_line = json.dumps(log_entry, ensure_ascii=False)
        
        # Log baseado no nível
        if level == "ERROR":
            self.logger.error(json_line)
        elif level == "WARNING":
            self.logger.warning(json_line)
        else:
            self.logger.info(json_line)
    
    def login_attempt(self, username: str, success: bool, ip: str, 
                     reason: Optional[str] = None):
        """
        Registra tentativa de login.
        
        Args:
            username: Nome de usuário
            success: Se login foi bem-sucedido
            ip: Endereço IP do cliente
            reason: Motivo da falha (se aplicável)
        """
        event_type = "login_success" if success else "login_failed"
        level = "INFO" if success else "WARNING"
        
        details = {
            "username": username,
            "ip": ip,
            "success": success
        }
        
        if reason:
            details["reason"] = reason
        
        self._log_event(event_type, details, level)
    
    def rate_limit_exceeded(self, endpoint: str, ip: str, limit: str):
        """
        Registra bloqueio por rate limit.
        
        Args:
            endpoint: Endpoint que foi bloqueado
            ip: Endereço IP bloqueado
            limit: Limite que foi excedido (ex: "5/minute")
        """
        self._log_event(
            "rate_limit_exceeded",
            {
                "endpoint": endpoint,
                "ip": ip,
                "limit": limit
            },
            "WARNING"
        )
    
    def validation_failed(self, field: str, value: str, reason: str, 
                         ip: str, endpoint: str):
        """
        Registra falha de validação suspeita.
        
        Args:
            field: Campo que falhou validação
            value: Valor que foi rejeitado (truncado se muito grande)
            reason: Motivo da rejeição
            ip: IP do cliente
            endpoint: Endpoint onde ocorreu
        """
        # Truncar valor se muito longo (evitar poluir logs)
        truncated_value = value[:100] + "..." if len(value) > 100 else value
        
        self._log_event(
            "validation_failed",
            {
                "field": field,
                "value": truncated_value,
                "reason": reason,
                "ip": ip,
                "endpoint": endpoint
            },
            "WARNING"
        )
    
    def access_denied(self, username: str, endpoint: str, required_role: str,
                     user_role: str, ip: str):
        """
        Registra tentativa de acesso negado.
        
        Args:
            username: Usuário que tentou acessar
            endpoint: Endpoint protegido
            required_role: Role necessária
            user_role: Role do usuário
            ip: IP do cliente
        """
        self._log_event(
            "access_denied",
            {
                "username": username,
                "endpoint": endpoint,
                "required_role": required_role,
                "user_role": user_role,
                "ip": ip
            },
            "WARNING"
        )
    
    def suspicious_activity(self, description: str, details: Dict[str, Any],
                          ip: str):
        """
        Registra atividade suspeita genérica.
        
        Args:
            description: Descrição da atividade suspeita
            details: Detalhes adicionais
            ip: IP do cliente
        """
        self._log_event(
            "suspicious_activity",
            {
                "description": description,
                "ip": ip,
                **details
            },
            "ERROR"
        )


# Instância global do logger de segurança
security_logger = SecurityLogger()