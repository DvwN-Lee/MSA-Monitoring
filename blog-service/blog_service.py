import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
from fastapi import Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session

from database import Base, SessionLocal, engine
from models import Post

# --- 기본 로깅 ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("BlogServiceApp")

app = FastAPI()

# --- 정적 파일 및 템플릿 설정 ---
templates = Jinja2Templates(directory="templates")
app.mount("/blog/static", StaticFiles(directory="static"), name="static")

# --- 설정 ---
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8002")


class PostRepository:
    """PostgreSQL 기반 게시글 저장소."""

    def __init__(self) -> None:
        self._ensure_schema()
        self._session_factory = SessionLocal

    async def list_posts(self, offset: int, limit: int) -> List[Dict]:
        def _list(session: Session) -> List[Dict]:
            stmt = (
                select(Post)
                .order_by(Post.id.desc())
                .offset(offset)
                .limit(limit)
            )
            posts = session.execute(stmt).scalars().all()
            return [self._to_dict(post) for post in posts]

        return await self._run_in_session(_list)

    async def get_post(self, post_id: int) -> Optional[Dict]:
        def _get(session: Session) -> Optional[Dict]:
            post = session.get(Post, post_id)
            return self._to_dict(post)

        return await self._run_in_session(_get)

    async def create_post(self, title: str, content: str, author: str) -> Dict:
        now = datetime.utcnow()

        def _create(session: Session) -> Dict:
            post = Post(
                title=title,
                content=content,
                author=author,
                created_at=now,
                updated_at=now,
            )
            session.add(post)
            session.commit()
            session.refresh(post)
            return self._to_dict(post)

        return await self._run_in_session(_create)

    async def update_post(self, post_id: int, data: Dict[str, str]) -> Optional[Dict]:
        def _update(session: Session) -> Optional[Dict]:
            post = session.get(Post, post_id)
            if not post:
                return None
            for key, value in data.items():
                setattr(post, key, value)
            post.updated_at = datetime.utcnow()
            session.commit()
            session.refresh(post)
            return self._to_dict(post)

        return await self._run_in_session(_update)

    async def delete_post(self, post_id: int) -> bool:
        def _delete(session: Session) -> bool:
            post = session.get(Post, post_id)
            if not post:
                return False
            session.delete(post)
            session.commit()
            return True

        return await self._run_in_session(_delete)

    async def count_posts(self) -> int:
        def _count(session: Session) -> int:
            stmt = select(func.count(Post.id))
            return session.execute(stmt).scalar_one()

        return await self._run_in_session(_count)

    async def ensure_seed_data(self, samples: List[Dict[str, str]]) -> None:
        def _seed(session: Session) -> None:
            current = session.execute(select(func.count(Post.id))).scalar_one()
            if current:
                return
            for sample in samples:
                post = Post(
                    title=sample["title"],
                    content=sample["content"],
                    author=sample["author"],
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                session.add(post)
            session.commit()

        await self._run_in_session(_seed)

    async def _run_in_session(self, fn):
        def _wrapper():
            with self._session_factory() as session:
                return fn(session)

        try:
            return await asyncio.to_thread(_wrapper)
        except SQLAlchemyError as exc:
            logger.error("Database operation failed: %s", exc, exc_info=True)
            raise

    @staticmethod
    def _to_dict(post: Optional[Post]) -> Optional[Dict]:
        if not post:
            return None
        return {
            "id": post.id,
            "title": post.title,
            "content": post.content,
            "author": post.author,
            "created_at": post.created_at.isoformat() if post.created_at else None,
            "updated_at": post.updated_at.isoformat() if post.updated_at else None,
        }

    @staticmethod
    def _ensure_schema(attempts: int = 10, backoff_seconds: int = 3) -> None:
        for attempt in range(1, attempts + 1):
            try:
                Base.metadata.create_all(bind=engine)
                return
            except OperationalError as exc:
                logger.warning(
                    "Waiting for PostgreSQL (attempt %s/%s): %s",
                    attempt,
                    attempts,
                    exc,
                )
                if attempt == attempts:
                    raise
                time.sleep(backoff_seconds * attempt)


repository = PostRepository()
users_db: Dict[str, Dict[str, str]] = {}


# --- Pydantic 모델 ---
class UserLogin(BaseModel):
    username: str
    password: str


class UserRegister(BaseModel):
    username: str
    password: str


class PostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=120)
    content: str = Field(..., min_length=1, max_length=20000)


class PostUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=120)
    content: Optional[str] = Field(None, min_length=1, max_length=20000)


# --- 인증 유틸 ---
async def require_user(request: Request) -> str:
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header missing or invalid")
    token = auth_header.split(" ")[1]
    verify_url = f"{AUTH_SERVICE_URL}/verify"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(verify_url, headers={"Authorization": f"Bearer {token}"}) as resp:
                data = await resp.json()
                if resp.status != 200 or data.get("status") != "success":
                    raise HTTPException(status_code=401, detail="Invalid or expired token")
                username = data.get("data", {}).get("username")
                if not username:
                    raise HTTPException(status_code=401, detail="Invalid token payload")
                return username
    except aiohttp.ClientError:
        raise HTTPException(status_code=502, detail="Auth service not reachable")


# --- API 핸들러 함수 ---
@app.get("/api/posts")
async def handle_get_posts(offset: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100)):
    """모든 블로그 게시물 목록을 반환합니다(최신순, 페이지네이션)."""
    items = await repository.list_posts(offset, limit)
    summaries = []
    for post in items:
        content = (post.get("content") or "").replace("\r", " ").replace("\n", " ")
        excerpt = content[:120] + ("..." if len(content) > 120 else "")
        summaries.append(
            {
                "id": post["id"],
                "title": post["title"],
                "author": post["author"],
                "created_at": post["created_at"],
                "excerpt": excerpt,
            }
        )
    return JSONResponse(content=summaries)


@app.get("/api/posts/{post_id}")
async def handle_get_post_by_id(post_id: int):
    """ID로 특정 게시물을 찾아 반환합니다."""
    post = await repository.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail={"error": "Post not found"})
    return JSONResponse(content=post)


@app.post("/api/login")
async def handle_login(user_login: UserLogin):
    """사용자 로그인을 처리합니다."""
    user = users_db.get(user_login.username)
    if user and user["password"] == user_login.password:
        return JSONResponse(content={"token": f"session-token-for-{user_login.username}"})
    raise HTTPException(status_code=401, detail={"error": "Invalid credentials"})


@app.post("/api/register", status_code=201)
async def handle_register(user_register: UserRegister):
    """사용자 등록을 처리합니다."""
    if not user_register.username or not user_register.password:
        raise HTTPException(status_code=400, detail={"error": "Username and password are required"})
    if user_register.username in users_db:
        raise HTTPException(status_code=409, detail={"error": "Username already exists"})

    users_db[user_register.username] = {"password": user_register.password}
    logger.info("New user registered: %s", user_register.username)
    return JSONResponse(content={"message": "Registration successful"})


@app.post("/api/posts", status_code=201)
async def create_post(request: Request, payload: PostCreate, username: str = Depends(require_user)):
    post = await repository.create_post(payload.title, payload.content, username)
    return JSONResponse(content=post)


@app.patch("/api/posts/{post_id}")
async def update_post_partial(post_id: int, request: Request, payload: PostUpdate, username: str = Depends(require_user)):
    existing = await repository.get_post(post_id)
    if not existing:
        raise HTTPException(status_code=404, detail={"error": "Post not found"})
    if existing["author"] != username:
        raise HTTPException(status_code=403, detail="Forbidden: not the author")

    update_data = payload.dict(exclude_unset=True, exclude_none=True)
    if not update_data:
        return JSONResponse(content={"message": "No changes"})

    updated = await repository.update_post(post_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail={"error": "Post not found"})
    return JSONResponse(content=updated)


@app.delete("/api/posts/{post_id}", status_code=204)
async def delete_post(post_id: int, request: Request, username: str = Depends(require_user)):
    existing = await repository.get_post(post_id)
    if not existing:
        raise HTTPException(status_code=404, detail={"error": "Post not found"})
    if existing["author"] != username:
        raise HTTPException(status_code=403, detail="Forbidden: not the author")

    deleted = await repository.delete_post(post_id)
    if not deleted:
        raise HTTPException(status_code=404, detail={"error": "Post not found"})
    return Response(status_code=204)


@app.get("/health")
async def handle_health():
    """쿠버네티스를 위한 헬스 체크 엔드포인트"""
    return {"status": "ok", "service": "blog-service"}


@app.get("/stats")
async def handle_stats():
    """대시보드를 위한 통계 엔드포인트"""
    post_count = await repository.count_posts()
    return {
        "blog_service": {
            "service_status": "online",
            "post_count": post_count,
        }
    }


# --- 웹 페이지 서빙 (SPA) ---
@app.get("/blog/{path:path}")
async def serve_spa(request: Request, path: str):
    """메인 블로그 페이지를 렌더링합니다."""
    return templates.TemplateResponse("index.html", {"request": request})


# --- 애플리케이션 시작 시 샘플 데이터 설정 ---
@app.on_event("startup")
async def setup_sample_data():
    """서비스 시작 시 샘플 데이터를 생성합니다."""
    global users_db
    users_db = {
        "admin": {"password": "password123"},
        "dev": {"password": "devpass"},
    }
    samples = [
        {
            "title": "첫 번째 블로그 글",
            "author": "admin",
            "content": "마이크로서비스 아키텍처에 오신 것을 환영합니다! 이 블로그는 FastAPI와 PostgreSQL을 사용합니다.",
        },
        {
            "title": "Kustomize와 Skaffold 활용하기",
            "author": "dev",
            "content": "인프라 관리를 자동화하고 배포 파이프라인을 개선하는 방법을 소개합니다.",
        },
    ]
    await repository.ensure_seed_data(samples)
    post_count = await repository.count_posts()
    logger.info(
        "%d개의 게시물과 %d명의 사용자로 초기화되었습니다.",
        post_count,
        len(users_db),
    )


if __name__ == "__main__":
    import uvicorn

    port = 8005
    logger.info("✅ Blog Service starting on http://0.0.0.0:%s", port)
    uvicorn.run(app, host="0.0.0.0", port=port)
