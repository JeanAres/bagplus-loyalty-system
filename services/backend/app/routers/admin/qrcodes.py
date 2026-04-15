"""
Endpoints administrativos - Geração de QR Codes
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db import models
from app.middleware.auth import require_role
from app.core.qrcode_generator import (
    gerar_lote_qrcodes,
    ler_ultimo_id,
    STORAGE_DIR
)
from app.core.audit import registrar_log
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import os

router = APIRouter(
    prefix="/api/admin/qrcodes",
    tags=["Admin - QR Codes"],
)


class GerarLoteRequest(BaseModel):
    """Request para gerar lote de QR Codes"""
    quantidade: int = Field(..., ge=1, le=10000, description="Quantidade de QR Codes (1 a 10.000)")
    data_criacao: Optional[str] = Field(None, description="Data de criação (YYYY-MM-DD). Default: hoje")
    formatos: List[str] = Field(default=["csv", "pdf"], description="Formatos a gerar: 'csv', 'pdf' ou ambos")
    
    @validator('data_criacao', pre=True, always=True)
    def validar_data(cls, v):
        """Valida e normaliza data_criacao"""
        # Se vier "string" ou vazio, retornar None (usa data de hoje)
        if not v or v == "string" or v == "":
            return None
        
        # Se vier data, validar formato YYYY-MM-DD
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError("Data deve estar no formato YYYY-MM-DD (ex: 2026-04-15)")


@router.get(
    "/ultimo-id",
    summary="Consultar último ID gerado"
)
def consultar_ultimo_id(
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Retorna o último ID de QR Code gerado no sistema.
    
    **Quando usar:**
    - Verificar próximo ID antes de gerar lote
    - Auditoria de controle de sequência
    - Planejamento de impressão
    
    **Retorna:**
    - ultimo_id: Último ID usado (0 se nenhum gerado ainda)
    - proximo_id: Próximo ID que será gerado
    - proximo_intervalo: Exemplo do próximo lote
    """
    ultimo_id = ler_ultimo_id()
    proximo_id = ultimo_id + 1
    
    return {
        "ultimo_id": ultimo_id,
        "ultimo_gerado": f"BAG-{ultimo_id:05d}" if ultimo_id > 0 else "Nenhum",
        "proximo_id": proximo_id,
        "proximo_gerado": f"BAG-{proximo_id:05d}",
        "exemplo_lote_100": f"BAG-{proximo_id:05d} até BAG-{proximo_id + 99:05d}"
    }


@router.post(
    "/gerar",
    summary="Gerar lote de QR Codes"
)
def gerar_lote(
    dados: GerarLoteRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Gera um novo lote de QR Codes sequenciais.
    
    **AUTENTICAÇÃO:**
    - Apenas administradores podem gerar QR Codes
    - Ação registrada em log de auditoria
    
    **PARÂMETROS:**
    - quantidade: Número de QR Codes (1 a 10.000)
    - data_criacao: Data opcional (YYYY-MM-DD). Deixe vazio para usar hoje
    - formatos: ["csv"], ["pdf"] ou ["csv", "pdf"]
    
    **COMPORTAMENTO:**
    - IDs são sequenciais e NUNCA se repetem
    - Cada ambiente (local/staging/prod) mantém sua própria sequência
    - CSV contém dados completos para importação no banco
    - PDF formatado para impressão em gráfica
    
    **RETORNA:**
    - Informações do lote gerado
    - Links para download dos arquivos
    - Intervalo de IDs gerados
    
    **EXEMPLO:**
    json
    {
      "quantidade": 100,
      "formatos": ["csv", "pdf"]
    }

    
    **IMPORTANTE:**
    - Após gerar, importe o CSV no banco via /api/admin/sacolas/importar-lote
    - Guarde o PDF para enviar à gráfica
    - Não gere lotes duplicados (IDs são únicos no sistema)
    """
    
    # Pegar SECRET_KEY do ambiente
    from app.core.security import SECRET_KEY
    
    if not SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Configuração inválida: SECRET_KEY não encontrada"
        )
    
    try:
        # Gerar lote
        resultado = gerar_lote_qrcodes(
            quantidade=dados.quantidade,
            secret_key=SECRET_KEY,
            data_criacao=dados.data_criacao,
            formatos=dados.formatos
        )
        
        # Registrar log de auditoria
        terminal = getattr(current_user, 'terminal', None)
        
        registrar_log(
            db=db,
            usuario=current_user,
            acao="gerar_qrcodes",
            entidade_tipo="QRCode",
            entidade_id=resultado["intervalo"],
            detalhes={
                "quantidade": resultado["quantidade"],
                "inicio": resultado["inicio"],
                "fim": resultado["fim"],
                "data_criacao": resultado["data_criacao"],
                "formatos": dados.formatos,
                "terminal": terminal
            },
            ip_address=request.client.host if request.client else None
        )
        db.commit()
        
        # Montar links de download
        links_download = {}
        
        if resultado["arquivos"]["csv"]:
            filename = os.path.basename(resultado["arquivos"]["csv"])
            links_download["csv"] = f"/api/admin/qrcodes/download/csv/{filename}"
        
        if resultado["arquivos"]["pdf"]:
            filename = os.path.basename(resultado["arquivos"]["pdf"])
            links_download["pdf"] = f"/api/admin/qrcodes/download/pdf/{filename}"
        
        return {
            "sucesso": True,
            "mensagem": f"Lote de {resultado['quantidade']} QR Codes gerado com sucesso",
            "quantidade": resultado["quantidade"],
            "intervalo": resultado["intervalo"],
            "data_criacao": resultado["data_criacao"],
            "formatos_gerados": [k for k, v in resultado["arquivos"].items() if v],
            "links_download": links_download,
            "proximo_id": resultado["fim"] + 1,
            "proximo_formato": f"BAG-{resultado['fim'] + 1:05d}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar QR Codes: {str(e)}"
        )


@router.get(
    "/download/{tipo}/{filename}",
    summary="Download de arquivo gerado"
)
def download_arquivo(
    tipo: str,
    filename: str,
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Faz download de arquivo CSV ou PDF gerado.
    
    **PARÂMETROS:**
    - tipo: "csv" ou "pdf"
    - filename: Nome do arquivo
    
    **AUTENTICAÇÃO:**
    - Admin e gerente podem baixar
    
    **RETORNA:**
    - Arquivo para download
    """
    # Validar tipo
    if tipo not in ["csv", "pdf"]:
        raise HTTPException(status_code=400, detail="Tipo inválido. Use 'csv' ou 'pdf'")
    
    # Validar filename (segurança: evitar path traversal)
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido")
    
    # Construir caminho
    file_path = os.path.join(STORAGE_DIR, tipo, filename)
    
    # Verificar se existe
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")
    
    # Retornar arquivo
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/octet-stream"
    )


@router.get(
    "/historico",
    summary="Histórico de lotes gerados"
)
def historico_lotes(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(require_role(["admin", "gerente"]))
):
    """
    Retorna histórico de lotes de QR Codes gerados.
    
    **INFORMAÇÕES:**
    - Baseado nos logs de auditoria
    - Mostra quem gerou, quando e quantos
    
    **QUANDO USAR:**
    - Auditoria de geração
    - Rastreamento de lotes
    - Análise de uso
    """
    logs = db.query(models.LogAuditoria).filter(
        models.LogAuditoria.acao == "gerar_qrcodes"
    ).order_by(
        models.LogAuditoria.data_hora.desc()
    ).limit(50).all()
    
    historico = []
    
    for log in logs:
        import json
        detalhes = json.loads(log.detalhes) if log.detalhes else {}
        
        usuario_info = db.query(models.Usuario).filter(
            models.Usuario.id == log.usuario_id
        ).first()
        
        historico.append({
            "data_hora": log.data_hora,
            "usuario": {
                "username": log.usuario_username,
                "nome": usuario_info.nome if usuario_info else None
            },
            "quantidade": detalhes.get("quantidade"),
            "intervalo": log.entidade_id,
            "data_criacao": detalhes.get("data_criacao"),
            "formatos": detalhes.get("formatos"),
            "terminal": detalhes.get("terminal"),
            "ip": log.ip_address
        })
    
    return {
        "total": len(historico),
        "lotes": historico
    }