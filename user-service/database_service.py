import asyncio
import logging
import time
from typing import Dict, Optional

from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from sqlalchemy.orm import Session
from werkzeug.security import check_password_hash, generate_password_hash

from database import Base, SessionLocal, engine
from models import User

logger = logging.getLogger(__name__)


class UserServiceDatabase:
    """데이터베이스 접근 레이어. SQLAlchemy 세션을 스레드 풀에서 실행한다."""

    def __init__(self):
        self._ensure_schema()
        self._session_factory = SessionLocal

    async def add_user(self, username: str, email: str, password: str) -> Optional[int]:
        password_hash = generate_password_hash(password)

        def _add(session: Session) -> Optional[int]:
            user = User(username=username, email=email, password_hash=password_hash)
            session.add(user)
            try:
                session.commit()
            except IntegrityError:
                session.rollback()
                return None
            session.refresh(user)
            return user.id

        return await self._run_in_session(_add)

    async def get_user_by_username(self, username: str) -> Optional[Dict]:
        def _fetch(session: Session) -> Optional[Dict]:
            result = session.execute(select(User).where(User.username == username))
            user = result.scalars().first()
            return self._to_dict(user)

        return await self._run_in_session(_fetch)

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        def _fetch(session: Session) -> Optional[Dict]:
            result = session.get(User, user_id)
            return self._to_dict(result)

        return await self._run_in_session(_fetch)

    async def verify_user_credentials(self, username: str, password: str) -> Optional[Dict]:
        def _verify(session: Session) -> Optional[Dict]:
            result = session.execute(select(User).where(User.username == username))
            user = result.scalars().first()
            if user and check_password_hash(user.password_hash, password):
                return self._to_dict(user)
            return None

        return await self._run_in_session(_verify)

    async def health_check(self) -> bool:
        try:
            def _ping(session: Session) -> bool:
                session.execute(text("SELECT 1"))
                return True

            return await self._run_in_session(_ping)
        except SQLAlchemyError as exc:
            logger.error("Database health check failed: %s", exc)
            return False

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
    def _to_dict(user: Optional[User]) -> Optional[Dict]:
        if not user:
            return None
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        }

    @staticmethod
    def _ensure_schema(attempts: int = 10, backoff_seconds: int = 3) -> None:
        for attempt in range(1, attempts + 1):
            try:
                Base.metadata.create_all(bind=engine)
                return
            except OperationalError as exc:
                logger.warning(
                    "Database not ready (attempt %s/%s): %s",
                    attempt,
                    attempts,
                    exc,
                )
                if attempt == attempts:
                    raise
                time.sleep(backoff_seconds * attempt)
