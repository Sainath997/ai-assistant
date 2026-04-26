"""Run the AI Assistant backend."""

import uvicorn
from agent.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_level="info",
    )
