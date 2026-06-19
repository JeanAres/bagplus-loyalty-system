"""
Middleware de headers de segurança HTTP

Este middleware adiciona headers de segurança em TODAS as respostas da API,
protegendo contra ataques comuns de segurança web.

Headers são instruções que o servidor envia para o navegador indicando
como ele deve se comportar ao processar a resposta.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adiciona headers de segurança em todas as respostas HTTP.
    
    Como funciona:
    1. Requisição chega → passa pelo middleware
    2. Middleware chama o endpoint (call_next)
    3. Endpoint processa e retorna resposta
    4. Middleware adiciona headers de segurança na resposta
    5. Resposta é enviada ao cliente com headers adicionados
    
    Nota sobre performance:
    BaseHTTPMiddleware tem overhead conhecido em aplicações de alta escala.
    Para este caso (apenas adição de headers), o impacto é mínimo (<1ms).
    Se necessário otimizar, migrar para middleware ASGI puro no futuro.
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Processa cada requisição/resposta adicionando headers de segurança.
        
        Args:
            request: Requisição HTTP recebida
            call_next: Função que chama o próximo handler (endpoint)
        
        Returns:
            Response com headers de segurança adicionados
        """
        # Chama o endpoint e obtém a resposta
        response = await call_next(request)
        
        # ========================================
        # PROTEÇÃO CONTRA MIME SNIFFING
        # ========================================
        # Previne: Navegador "adivinhar" tipo de arquivo incorretamente
        # Exemplo de ataque: Arquivo .txt com código JavaScript sendo executado
        # Resultado: Navegador respeita o Content-Type enviado pelo servidor
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # ========================================
        # PROTEÇÃO CONTRA CLICKJACKING
        # ========================================
        # Previne: Site malicioso embutir nossa API em iframe invisível
        # Exemplo de ataque: Usuário clica em botão "like" mas na verdade está
        #                    transferindo dinheiro em iframe oculto
        # Resultado: Navegador recusa carregar site em iframe
        response.headers["X-Frame-Options"] = "DENY"
        
        # ========================================
        # PROTEÇÃO DE PRIVACIDADE - REFERRER
        # ========================================
        # Controla: Quanta informação é enviada no header "Referer"
        # Exemplo: Usuário em https://admin.bagplus.com.br/cliente/12345678900
        #          clica em link externo
        # Sem proteção: Site externo recebe URL completa (vaza CPF!)
        # Com proteção: Site externo recebe apenas https://admin.bagplus.com.br
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # ========================================
        # PROTEÇÃO CONTRA ADOBE FLASH/PDF
        # ========================================
        # Previne: Produtos Adobe (Flash, PDF) acessarem conteúdo
        # Contexto: Flash tinha vulnerabilidades críticas
        # Resultado: Nenhum produto Adobe pode fazer requisições cross-domain
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        
       # ========================================
        # CONTENT SECURITY POLICY (CSP)
        # ========================================
        # Define: O que pode ser carregado e executado na página
        # Proteção principal contra: XSS (Cross-Site Scripting)
        
        # CSP diferenciado por tipo de endpoint:
        if request.url.path.startswith("/docs") or request.url.path.startswith("/redoc"):
            # CSP PERMISSIVO para Swagger/ReDoc (documentação interativa)
            # Swagger/ReDoc precisam de recursos externos e inline para funcionar
            # unsafe-inline: CSS inline necessário para renderização
            # unsafe-eval: JavaScript dinâmico do Swagger
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' https:; "  # Permite HTTPS externo
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' data: https://fonts.gstatic.com; "
                "connect-src 'self' https:;"  # Permite fetch/XHR para CDNs
            )
        else:
            # CSP RESTRITIVO para endpoints de API
            # API retorna JSON/dados puros, não precisa carregar nada
            # Qualquer tentativa de carregar script/imagem é bloqueada
            response.headers["Content-Security-Policy"] = "default-src 'none'"
        
        # ========================================
        # HSTS (Strict-Transport-Security)
        # ========================================
        # IMPORTANTE: HSTS NÃO é configurado aqui!
        # 
        # Por quê?
        # - Nossa infraestrutura usa Nginx como proxy reverso
        # - Nginx faz SSL termination (converte HTTPS → HTTP interno)
        # - FastAPI recebe tráfego HTTP (internamente)
        # - request.url.scheme seria "http" mesmo com HTTPS externo
        # 
        # Onde configurar:
        # - No arquivo nginx.conf do servidor AWS
        # - Comando: add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
        # 
        # O que HSTS faz:
        # - Força navegador a SEMPRE usar HTTPS
        # - Previne downgrade para HTTP (ataque man-in-the-middle)
        # - Exemplo: http://api.bagplus.com.br → automaticamente vira https://
        
        return response