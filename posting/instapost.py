from __future__ import annotations

import mimetypes
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterable

import httpx
from dotenv import load_dotenv

load_dotenv()

ZERNIO_API_KEY = os.getenv("ZERNIO_API_KEY", "")
INSTAGRAM_ACCOUNT_ID = os.getenv("INSTAGRAM_ACCOUNT_ID", "")

API_BASE = "https://zernio.com/api"

_MAX_RETRIES = 3
_RETRY_DELAY = 2.0


def has_instagram_api_config() -> bool:
    return bool(ZERNIO_API_KEY.strip())


def upload_carousel(image_paths: Iterable[str], caption: str = "") -> dict:
    paths = _resolve_paths(image_paths)
    provider: InstagramProvider = ZernioMCPProvider()
    return provider.publish(paths, caption)


def upload_reel(video_path: str, caption: str = "") -> dict:
    if not video_path or not Path(video_path).exists():
        raise FileNotFoundError(f"Video path does not exist: {video_path}")
    provider: InstagramProvider = ZernioMCPProvider()
    return provider.publish_reel(video_path, caption)


def _resolve_paths(image_paths: Iterable[str]) -> list[str]:
    paths = [str(p).strip() for p in image_paths if str(p).strip()]
    for p in paths:
        if not Path(p).exists():
            raise FileNotFoundError(f"Image path does not exist: {p}")
    if not paths:
        raise ValueError("No valid image paths provided.")
    return paths[:10]


class InstagramProvider(ABC):
    @abstractmethod
    def publish(self, paths: list[str], caption: str) -> dict: ...

    def publish_reel(self, video_path: str, caption: str) -> dict:
        raise NotImplementedError("Reel posting not supported by this provider")


class ZernioMCPProvider(InstagramProvider):
    def publish(self, paths: list[str], caption: str) -> dict:
        media_urls = self._upload_media(paths)
        return self._create_post_api(media_urls, caption)

    def publish_reel(self, video_path: str, caption: str) -> dict:
        media_url = self._upload_video(video_path)
        return self._create_reel_api(media_url, caption)

    def _headers(self) -> dict[str, str]:
        return {"Authorization": f"Bearer {ZERNIO_API_KEY}"}

    def _auth_json(self) -> dict[str, str]:
        h = self._headers()
        h["Content-Type"] = "application/json"
        return h

    def _upload_media(self, paths: list[str]) -> list[str]:
        url = f"{API_BASE}/v1/media"
        urls = []
        for p in paths:
            path = Path(p)
            mime = mimetypes.guess_type(p)[0] or "image/jpeg"
            data = path.read_bytes()

            for attempt in range(_MAX_RETRIES):
                try:
                    with httpx.Client(timeout=120.0) as client:
                        files = {"files": (path.name, data, mime)}
                        resp = client.post(url, headers=self._headers(), files=files)
                        resp.raise_for_status()
                        result = resp.json()
                    file_urls = [f["url"] for f in result.get("files", [])]
                    if not file_urls:
                        raise RuntimeError(f"Zernio returned no URL for {path.name}")
                    urls.append(file_urls[0])
                    break
                except httpx.HTTPStatusError as e:
                    body = e.response.text[:500] if e.response else str(e)
                    if attempt == _MAX_RETRIES - 1:
                        raise RuntimeError(f"Upload failed for {path.name} after {_MAX_RETRIES} retries: {body}") from e
                    print(f"[instapost] Upload attempt {attempt + 1} failed for {path.name}, retrying...")
                    time.sleep(_RETRY_DELAY * (attempt + 1))
                except httpx.RequestError as e:
                    if attempt == _MAX_RETRIES - 1:
                        raise RuntimeError(f"Upload network error for {path.name}: {e}") from e
                    time.sleep(_RETRY_DELAY * (attempt + 1))

        print(f"[instapost] Uploaded {len(urls)} media file(s) to Zernio")
        return urls

    def _upload_video(self, video_path: str) -> str:
        url = f"{API_BASE}/v1/media"
        path = Path(video_path)
        mime = "video/mp4"
        data = path.read_bytes()

        for attempt in range(_MAX_RETRIES):
            try:
                with httpx.Client(timeout=300.0) as client:
                    files = {"files": (path.name, data, mime)}
                    resp = client.post(url, headers=self._headers(), files=files)
                    resp.raise_for_status()
                    result = resp.json()
                file_urls = [f["url"] for f in result.get("files", [])]
                if not file_urls:
                    raise RuntimeError(f"Zernio returned no URL for {path.name}")
                print(f"[instapost] Uploaded video to Zernio: {file_urls[0]}")
                return file_urls[0]
            except httpx.HTTPStatusError as e:
                body = e.response.text[:500] if e.response else str(e)
                if attempt == _MAX_RETRIES - 1:
                    raise RuntimeError(f"Video upload failed after {_MAX_RETRIES} retries: {body}") from e
                print(f"[instapost] Video upload attempt {attempt + 1} failed, retrying...")
                time.sleep(_RETRY_DELAY * (attempt + 1))
            except httpx.RequestError as e:
                if attempt == _MAX_RETRIES - 1:
                    raise RuntimeError(f"Video upload network error: {e}") from e
                time.sleep(_RETRY_DELAY * (attempt + 1))

        raise RuntimeError("Unexpected error in _upload_video")

    def _get_instagram_account_id(self) -> str:
        if INSTAGRAM_ACCOUNT_ID.strip():
            return INSTAGRAM_ACCOUNT_ID.strip()
        url = f"{API_BASE}/v1/accounts"
        for attempt in range(_MAX_RETRIES):
            try:
                with httpx.Client(timeout=15.0) as client:
                    resp = client.get(url, headers=self._headers(), params={"platform": "instagram"})
                    resp.raise_for_status()
                    data = resp.json()
                accounts = data.get("accounts", data.get("data", []))
                if not accounts:
                    raise RuntimeError("No Instagram account found in Zernio. Connect one at https://zernio.com or set INSTAGRAM_ACCOUNT_ID in .env")
                return accounts[0].get("id", accounts[0].get("_id", ""))
            except httpx.HTTPStatusError as e:
                if attempt == _MAX_RETRIES - 1:
                    raise RuntimeError(f"Failed to list Zernio accounts: {e.response.text[:500]}") from e
                time.sleep(_RETRY_DELAY * (attempt + 1))
            except httpx.RequestError as e:
                if attempt == _MAX_RETRIES - 1:
                    raise RuntimeError(f"Zernio accounts network error: {e}") from e
                time.sleep(_RETRY_DELAY * (attempt + 1))

    def _create_post_api(self, media_urls: list[str], caption: str) -> dict:
        url = f"{API_BASE}/v1/posts"
        account_id = self._get_instagram_account_id()
        platforms: list[dict[str, str]] = [{"platform": "instagram", "accountId": account_id}]

        payload: dict[str, Any] = {
            "content": caption,
            "platforms": platforms,
            "mediaItems": [{"type": "image", "url": u} for u in media_urls],
            "publishNow": True,
        }

        for attempt in range(_MAX_RETRIES):
            try:
                with httpx.Client(timeout=30.0) as client:
                    resp = client.post(url, headers=self._auth_json(), json=payload)
                    resp.raise_for_status()
                    data = resp.json()
            except httpx.HTTPStatusError as e:
                body = e.response.text[:500] if e.response else str(e)
                if attempt == _MAX_RETRIES - 1:
                    raise RuntimeError(f"Zernio API error: {body}") from e
                time.sleep(_RETRY_DELAY * (attempt + 1))
                continue
            except httpx.RequestError as e:
                if attempt == _MAX_RETRIES - 1:
                    raise RuntimeError(f"Zernio API network error: {e}") from e
                time.sleep(_RETRY_DELAY * (attempt + 1))
                continue

            post_status = "unknown"
            post_id = ""
            post = data.get("post", {})
            if post:
                post_status = post.get("status", "unknown")
                post_id = post.get("id", post.get("_id", ""))
            msg = data.get("message", data.get("msg", str(data)[:200]))
            print(f"[instapost] Zernio post created — id={post_id} status={post_status}")
            return {
                "status": post_status if post_status != "unknown" else "posted",
                "media_count": len(media_urls),
                "provider": "zernio_api",
                "post_id": post_id,
                "response": msg,
            }

        raise RuntimeError("Unexpected error in _create_post_api")

    def _create_reel_api(self, media_url: str, caption: str) -> dict:
        url = f"{API_BASE}/v1/posts"
        account_id = self._get_instagram_account_id()
        platforms: list[dict[str, str]] = [{"platform": "instagram", "accountId": account_id}]

        payload: dict[str, Any] = {
            "content": caption,
            "platforms": platforms,
            "mediaItems": [{"type": "video", "url": media_url}],
            "publishNow": True,
        }

        for attempt in range(_MAX_RETRIES):
            try:
                with httpx.Client(timeout=60.0) as client:
                    resp = client.post(url, headers=self._auth_json(), json=payload)
                    resp.raise_for_status()
                    data = resp.json()
            except httpx.HTTPStatusError as e:
                body = e.response.text[:500] if e.response else str(e)
                if attempt == _MAX_RETRIES - 1:
                    raise RuntimeError(f"Zernio API error: {body}") from e
                time.sleep(_RETRY_DELAY * (attempt + 1))
                continue
            except httpx.RequestError as e:
                if attempt == _MAX_RETRIES - 1:
                    raise RuntimeError(f"Zernio API network error: {e}") from e
                time.sleep(_RETRY_DELAY * (attempt + 1))
                continue

            post = data.get("post", {})
            post_status = post.get("status", "unknown") if post else "unknown"
            post_id = post.get("id", post.get("_id", "")) if post else ""
            msg = data.get("message", data.get("msg", str(data)[:200]))
            print(f"[instapost] Zernio reel created — id={post_id} status={post_status}")
            return {
                "status": post_status if post_status != "unknown" else "posted",
                "media_count": 1,
                "provider": "zernio_api",
                "post_id": post_id,
                "response": msg,
            }

        raise RuntimeError("Unexpected error in _create_reel_api")
