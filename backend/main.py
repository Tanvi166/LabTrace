from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base, is_sqlite_database
from app.api.v1 import auth, experiments, compare, rag, reports, agents, mcp, analysis_runs, search, chat, agent_chat, files

# Local SQLite stays zero-configuration. Azure SQL schema changes are applied
# explicitly through Alembic, never provisioned by application startup.
if is_sqlite_database():
    Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "storage_provider": settings.STORAGE_PROVIDER
    }

# Register API routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])
app.include_router(experiments.router, prefix=f"{settings.API_V1_STR}/experiments", tags=["Experiments"])
app.include_router(compare.router, prefix=f"{settings.API_V1_STR}/compare", tags=["Compare"])
app.include_router(rag.router, prefix=f"{settings.API_V1_STR}/rag", tags=["RAG Knowledge"])
app.include_router(reports.router, prefix=f"{settings.API_V1_STR}/reports", tags=["Reports"])
app.include_router(agents.router, prefix=f"{settings.API_V1_STR}/agents", tags=["Agents"])
app.include_router(mcp.router, prefix=f"{settings.API_V1_STR}/mcp", tags=["MCP Server"])
app.include_router(analysis_runs.router, prefix=f"{settings.API_V1_STR}/analysis-runs", tags=["Analysis Runs"])
app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["Azure AI Search"])
app.include_router(chat.router, prefix=f"{settings.API_V1_STR}/chat", tags=["RAG Chat"])
app.include_router(agent_chat.router, prefix=f"{settings.API_V1_STR}/agent", tags=["Foundry Agent Chat"])
app.include_router(files.router, prefix=f"{settings.API_V1_STR}/files", tags=["Azure Blob Files"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
