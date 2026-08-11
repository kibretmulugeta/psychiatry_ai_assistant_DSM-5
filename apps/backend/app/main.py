"""
FastAPI Backend Application Entrypoint.
Initializes middleware, CORS, logging, exception handlers, and routing for DSM-5 Psychiatry AI Assistant.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from apps.backend.app.api.router import api_router
from apps.backend.app.core.config import settings
from apps.backend.app.core.logging import get_logger, setup_logging
from packages.database.session import engine
from packages.shared.exceptions import BaseAppException

logger = get_logger("backend.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan context managing startup and shutdown tasks."""
    try:
        setup_logging(log_level=settings.LOG_LEVEL, is_dev=(settings.APP_ENV == "development"))
        logger.info(
            "starting_application",
            app_name=settings.APP_NAME,
            environment=settings.APP_ENV,
            active_llm=settings.ACTIVE_LLM_PROVIDER,
            active_embedding=settings.ACTIVE_EMBEDDING_PROVIDER,
        )
    except Exception as exc:
        print(f"Lifespan startup warning: {exc}")
    yield
    try:
        logger.info("shutting_down_application")
        await engine.dispose()
    except Exception:
        pass


def create_application() -> FastAPI:
    """FastAPI Application factory."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="Production-ready DSM-5 Psychiatry & Clinical Psychology AI Assistant & Clinical Decision Support Service",
        version="1.0.0",
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
        docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
        redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS Middleware configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register Domain Exception Handler
    @app.exception_handler(BaseAppException)
    async def custom_app_exception_handler(
        request: Request, exc: BaseAppException
    ) -> JSONResponse:
        logger.warning(f"domain_exception_raised code={exc.code} message={exc.message} path={request.url.path}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
        )

    # Global Exception Fallback Handler
    @app.exception_handler(Exception)
    async def global_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.error(f"unhandled_exception error={str(exc)} path={request.url.path}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred on the server.",
                "details": {},
            },
        )

    # Include API Routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    @app.get("/", tags=["System"])
    async def root():
        """Root endpoint returning API status."""
        return {
            "name": settings.APP_NAME,
            "status": "online",
            "version": "1.0.0",
            "message": "DSM-5 Psychiatry & Clinical Psychology AI Assistant API is active",
            "dsm_version": "DSM-5 / DSM-5-TR",
            "demo_url": "/demo"
        }

    from fastapi.responses import HTMLResponse, FileResponse
    from pathlib import Path

    WIDGET_DIR = Path(__file__).resolve().parent.parent.parent / "widget" / "src"

    @app.get("/widget.js", tags=["System"])
    async def get_widget_js():
        js_file = WIDGET_DIR / "widget.js"
        if not js_file.exists():
            js_file = WIDGET_DIR.parent / "dist" / "widget.js"
        if js_file.exists():
            return FileResponse(js_file, media_type="application/javascript", headers={"Cache-Control": "no-cache, no-store, must-revalidate, max-age=0"})
        return JSONResponse(status_code=404, content={"message": "Widget JS not found"})

    @app.get("/widget.css", tags=["System"])
    async def get_widget_css():
        css_file = WIDGET_DIR / "widget.css"
        if not css_file.exists():
            css_file = WIDGET_DIR.parent / "dist" / "widget.css"
        if css_file.exists():
            return FileResponse(css_file, media_type="text/css", headers={"Cache-Control": "no-cache, no-store, must-revalidate, max-age=0"})
        return JSONResponse(status_code=404, content={"message": "Widget CSS not found"})

    @app.get("/demo", response_class=HTMLResponse, tags=["System"])
    async def demo_ui():
        """Returns a live HTML page with the DSM-5 PsychAssist floating widget and dashboard."""
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>DSM-5 Psychiatry & Clinical Psychology AI Assistant</title>
          <link rel="preconnect" href="https://fonts.googleapis.com">
          <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
          <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
          <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: 'Inter', sans-serif; background: #0f172a; color: #f8fafc; min-height: 100vh; display: flex; flex-direction: column; align-items: center; justify-content: flex-start; padding: 40px 20px; }
            .header { text-align: center; max-width: 900px; margin-bottom: 30px; }
            .badge { display: inline-block; background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 20px; padding: 6px 16px; font-size: 0.85rem; font-weight: 600; margin-bottom: 15px; letter-spacing: 0.5px; }
            h1 { font-size: 2.4rem; font-weight: 700; background: linear-gradient(135deg, #818cf8 0%, #c084fc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-bottom: 12px; }
            p.sub { color: #94a3b8; font-size: 1.05rem; line-height: 1.6; }
            .features-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 20px; width: 100%; max-width: 1000px; margin-top: 30px; }
            .card { background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(255, 255, 255, 0.08); backdrop-filter: blur(12px); border-radius: 16px; padding: 24px; transition: transform 0.2s ease, border-color 0.2s ease; }
            .card:hover { transform: translateY(-4px); border-color: rgba(129, 140, 248, 0.4); }
            .card-icon { font-size: 1.8rem; margin-bottom: 12px; color: #818cf8; }
            .card h3 { font-size: 1.15rem; font-weight: 600; color: #f1f5f9; margin-bottom: 8px; }
            .card p { font-size: 0.9rem; color: #94a3b8; line-height: 1.5; }
            .crisis-banner { width: 100%; max-width: 1000px; background: rgba(225, 29, 72, 0.15); border: 1px solid rgba(225, 29, 72, 0.4); border-radius: 14px; padding: 18px 24px; margin-top: 30px; display: flex; align-items: center; justify-content: space-between; }
            .crisis-text h4 { color: #fda4af; font-size: 1rem; margin-bottom: 4px; }
            .crisis-text p { color: #fecdd3; font-size: 0.88rem; }
            .crisis-btn { background: #e11d48; color: white; border: none; border-radius: 8px; padding: 10px 18px; font-weight: 600; font-size: 0.88rem; cursor: pointer; text-decoration: none; transition: background 0.2s; }
            .crisis-btn:hover { background: #be123c; }
          </style>
          <link rel="stylesheet" href="/widget.css">
        </head>
        <body>
          <div class="header">
            <span class="badge">DSM-5 / DSM-5-TR SCIENTIFIC DECISION SUPPORT</span>
            <h1>DSM-5 Psychiatry & Clinical Psychology AI Assistant</h1>
            <p class="sub">Evidence-based diagnostic criteria, differential diagnosis pathways, epidemiological reference metrics, and psychometric screening tools grounded in official DSM-5 standards.</p>
          </div>

          <div class="features-grid">
            <div class="card">
              <div class="card-icon">📖</div>
              <h3>Diagnostic Criteria</h3>
              <p>Instant breakdown of DSM-5 diagnostic criteria (A, B, C...), specifiers, and ICD-10-CM codes for all major psychiatric disorders.</p>
            </div>
            <div class="card">
              <div class="card-icon">🔀</div>
              <h3>Differential Diagnosis</h3>
              <p>Clinical decision trees differentiating overlapping conditions (MDD vs Bipolar II, GAD vs Panic, PTSD vs Acute Stress).</p>
            </div>
            <div class="card">
              <div class="card-icon">📊</div>
              <h3>Statistical & Epidemiology</h3>
              <p>Empirical metrics on 12-month & lifetime prevalence, male-to-female ratios, median onset age, and genetic heritability.</p>
            </div>
            <div class="card">
              <div class="card-icon">📝</div>
              <h3>Psychometric Tools</h3>
              <p>Automated evaluation of validated screening scales including PHQ-9 (Depression), GAD-7 (Anxiety), and PCL-5 (PTSD).</p>
            </div>
          </div>

          <div class="crisis-banner">
            <div class="crisis-text">
              <h4>🚨 Immediate Crisis & Safety Support</h4>
              <p>If you or someone you know is in distress or experiencing suicidal ideation, help is available 24/7 (Free & Confidential).</p>
            </div>
            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
              <a href="tel:988" class="crisis-btn" onclick="window.open('https://988lifeline.org/chat/', '_blank')">Call or Text 988</a>
              <a href="https://findahelpline.com/" target="_blank" rel="noopener" class="crisis-btn" style="background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.3);">International Hotlines</a>
            </div>
          </div>

          <script src="/widget.js"></script>
          <script>
            WebsiteAssistant.init({
              apiKey: "dsm5-demo-key-12345",
              apiEndpoint: "/api/v1",
              theme: "dark",
              position: "bottom-right",
              primaryColor: "#6366f1",
              welcomeMessage: "Welcome to DSM-5 PsychAssist AI. Ask me about DSM-5 diagnostic criteria, differential diagnosis, prevalence statistics, or psychometric tools (PHQ-9, GAD-7)!"
            });
          </script>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)

    return app


app = create_application()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "apps.backend.app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
