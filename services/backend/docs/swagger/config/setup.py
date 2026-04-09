"""
Configuração customizada do Swagger UI
"""
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse

def configure_swagger_ui(app: FastAPI):
    """Configura Swagger UI customizado com tema dark"""
    
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        response = get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            swagger_ui_parameters=app.swagger_ui_parameters
        )
        
        html_content = response.body.decode("utf-8")
        
        # URLs para CSS customizado e Google Font
        custom_css_url = "/swagger-styles/dark.css"
        google_fonts_url = "https://fonts.googleapis.com/css2?family=Work+Sans:wght@300;400;500;600;700&display=swap"
        
        # Injetar CSS no HTML
        css_injection = f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="{google_fonts_url}" rel="stylesheet">
        <link type="text/css" rel="stylesheet" href="{custom_css_url}">
        </head>
        """
        
        html_content = html_content.replace("</head>", css_injection)
        
        return HTMLResponse(html_content)
    
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        """Documentação alternativa com ReDoc"""
        return get_redoc_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - ReDoc",
            redoc_favicon_url="https://fastapi.tiangolo.com/img/favicon.png"
        )