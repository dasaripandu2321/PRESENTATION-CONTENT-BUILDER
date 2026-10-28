import os
import uvicorn
from app.config import settings

if __name__ == "__main__":
    # Ensure telemetry disabled
    os.environ["ANONYMIZED_TELEMETRY"] = "False"
    os.environ["CHROMA_SERVER_NOOP_TELEMETRY"] = "True"

    print("=" * 70)
    print("   PRESENTATION CONTENT BUILDER AI • RAG + LLM ENGINE")
    print(f"   Server running at: http://{settings.HOST}:{settings.PORT}")
    print(f"   API Documentation: http://{settings.HOST}:{settings.PORT}/docs")
    print("=" * 70)

    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )

