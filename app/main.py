import os

from dotenv import load_dotenv
from fastapi import FastAPI


load_dotenv()

from config.database.session import Base, engine
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

CORS_ALLOWED_FRONTEND_URL = os.getenv("CORS_ALLOWED_FRONTEND_URL")


origins = [
    CORS_ALLOWED_FRONTEND_URL,  # Next.js 프론트 엔드 URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,       # 정확한 origin만 허용
    allow_credentials=True,      # 쿠키 허용
    allow_methods=["*"],         # 모든 HTTP 메서드 허용
    allow_headers=["*"],         # 모든 헤더 허용
)

# 앱 실행

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("APP_HOST")
    port = int(os.getenv("APP_PORT"))
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    uvicorn.run(app, host=host, port=port)