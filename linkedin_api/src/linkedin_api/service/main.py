from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..capabilities import analytics, discovery, engagement, feed, jobs, messaging, network, posting
from ..core import LinkedInClient, SessionHealth, Vault
from ..core.auth import authenticate
from ..core.errors import SessionExpiredError

logger = logging.getLogger(__name__)


class PostCreateRequest(BaseModel):
    text: str
    image_path: str | None = None


class CommentCreateRequest(BaseModel):
    post_urn: str
    text: str


class LikeRequest(BaseModel):
    post_urn: str


class MessageSendRequest(BaseModel):
    profile_urn: str
    message: str


class ConnectionSendRequest(BaseModel):
    profile_urn: str
    note: str | None = None


app = FastAPI(title="LinkedIn API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _client() -> LinkedInClient:
    return LinkedInClient()


def _vault() -> Vault:
    return Vault()


def _session() -> SessionHealth:
    return SessionHealth(_vault(), _client()._http)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/auth/login")
async def auth_login(
    username: str,
    password: str,
) -> dict[str, bool]:
    try:
        success = authenticate(username, password)
        return {"success": success}
    except Exception as e:
        logger.error("Auth login failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/auth/status")
async def auth_status() -> dict[str, Any]:
    session = _session()
    result = session.check()
    return {
        "valid": result["ok"],
        "status_code": result["status"],
        "message": result["message"],
    }


@app.post("/api/post")
async def create_post(
    text: str,
    image_path: str | None = None,
) -> dict[str, Any]:
    try:
        if image_path:
            result = posting.post_with_image(text, image_path, _client()._http, _vault())
        else:
            result = posting.post_text(text)
        return result
    except SessionExpiredError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error("Post creation failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/comment")
async def create_comment(
    post_urn: str,
    text: str,
) -> dict[str, str]:
    try:
        return engagement.comment(post_urn, text)
    except SessionExpiredError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error("Comment failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/like")
async def like_post(
    post_urn: str,
) -> dict[str, bool]:
    try:
        return engagement.like(post_urn)
    except SessionExpiredError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error("Like failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/message")
async def send_message(
    profile_urn: str,
    message: str,
) -> dict[str, str]:
    try:
        return messaging.send_dm(profile_urn, message)
    except SessionExpiredError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error("Send message failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/connection")
async def send_connection(
    profile_urn: str,
    note: str | None = None,
) -> dict[str, str]:
    try:
        return network.send_connection_request(profile_urn, note, _client(), _vault())
    except SessionExpiredError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error("Connection request failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/feed")
async def get_feed(
    limit: int = 20,
) -> dict[str, Any]:
    try:
        return {"feed": feed.get_my_feed(limit)}
    except SessionExpiredError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error("Feed fetch failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/insights/{post_urn}")
async def get_insights(
    post_urn: str,
) -> dict[str, int]:
    try:
        return analytics.get_post_insights(post_urn)
    except SessionExpiredError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error("Post insights failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/search/people")
async def search_people(
    q: str,
    limit: int = 10,
) -> dict[str, Any]:
    try:
        return {"results": discovery.search_people(q, limit, _client(), _vault())}
    except SessionExpiredError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error("People search failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/profile/{urn_or_url}")
async def get_profile(
    urn_or_url: str,
) -> dict[str, Any]:
    try:
        return discovery.get_profile(urn_or_url, _client(), _vault())
    except SessionExpiredError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error("Profile fetch failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/api/jobs/search")
async def search_jobs(
    q: str,
    location: str | None = None,
) -> dict[str, Any]:
    try:
        return {"jobs": jobs.search_jobs(q, location)}
    except SessionExpiredError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error("Job search failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/api/jobs/{job_id}/bookmark")
async def bookmark_job(
    job_id: str,
) -> dict[str, bool]:
    try:
        return jobs.bookmark_job(job_id)
    except SessionExpiredError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        logger.error("Job bookmark failed: %s", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))