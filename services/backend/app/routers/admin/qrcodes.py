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
from datetime import datetime
import os
import json

router = APIRouter(
    prefix="/api/admin/qrcodes",
    tags=["Admin - QR Codes"],
)


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
    quantidade: int,
    request: Request,
    db: Session = Depends(get_db),
    data_criacao: str = None,
    gerar_csv: bool = True,
    gerar_pdf: bool = True,
    current_user: models.Usuario = Depends(require_role(["admin"]))
):
    """
    Gera um novo lote de QR Codes sequenciais.

    **Permissão:** Admin

    **Parâmetros:**
    - quantidade: Número de QR Codes (1 a 10.000)
    - data_criacao: Data opcional (YYYY-MM-DD). Deixe vazio para usar hoje
    - gerar_csv: Gerar arquivo CSV para importação (padrão: true)
    - gerar_pdf: Gerar arquivo PDF para impressão (padrão: true)

    **Observação:** Após gerar, importe o CSV via /api/admin/lotes/importar
    """

    from app.core.security import SECRET_KEY

    if not SECRET_KEY:
        raise HTTPException(
            status_code=500,
            detail="Configuração inválida: SECRET_KEY não encontrada"
        )

    if quantidade < 1 or quantidade > 10000:
        raise HTTPException(
            status_code=400,
            detail="Quantidade deve ser entre 1 e 10.000"
        )

    if data_criacao:
        try:
            datetime.strptime(data_criacao, '%Y-%m-%d')
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Data deve estar no formato YYYY-MM-DD (ex: 2026-04-15)"
            )

    formatos = []
    if gerar_csv:
        formatos.append("csv")
    if gerar_pdf:
        formatos.append("pdf")

    if not formatos:
        raise HTTPException(
            status_code=400,
            detail="Selecione pelo menos um formato (gerar_csv ou gerar_pdf)"
        )

    try:
        resultado = gerar_lote_qrcodes(
            quantidade=quantidade,
            secret_key=SECRET_KEY,
            data_criacao=data_criacao,
            formatos=formatos
        )

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
                "formatos": formatos,
                "terminal": terminal
            },
            ip_address=request.client.host if request.client else None
        )
        db.commit()

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

    **Permissão:** Admin ou Gerente

    **Parâmetros:**
    - tipo: "csv" ou "pdf"
    - filename: Nome do arquivo
    """

    if tipo not in ["csv", "pdf"]:
        raise HTTPException(status_code=400, detail="Tipo inválido. Use 'csv' ou 'pdf'")

    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Nome de arquivo inválido")

    file_path = os.path.join(STORAGE_DIR, tipo, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

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

    **Permissão:** Admin ou Gerente

    **Informações:**
    - Baseado nos logs de auditoria
    - Mostra quem gerou, quando e quantos
    """

    logs = db.query(models.LogAuditoria).filter(
        models.LogAuditoria.acao == "gerar_qrcodes"
    ).order_by(
        models.LogAuditoria.timestamp.desc()
    ).limit(50).all()

    historico = []

    for log in logs:
        detalhes = json.loads(log.detalhes) if log.detalhes else {}

        usuario_info = db.query(models.Usuario).filter(
            models.Usuario.id == log.usuario_id
        ).first()

        historico.append({
            "data_hora": log.timestamp,
            "usuario": {
                "username": log.usuario.username if log.usuario else "sistema",
                "nome": usuario_info.nome if usuario_info else None
            },
            "quantidade": detalhes.get("quantidade"),
            "intervalo": detalhes.get("inicio"),
            "data_criacao": detalhes.get("data_criacao"),
            "formatos": detalhes.get("formatos"),
            "terminal": detalhes.get("terminal"),
            "ip": log.ip
        })

    return {
        "total": len(historico),
        "lotes": historico
    }