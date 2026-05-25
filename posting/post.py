from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

from config.config import append_log, get_config, get_selected_music
from .instapost import has_instagram_api_config, upload_carousel, upload_reel
from .reel import images_to_video


def post_to_instagram(image_paths: Iterable[str], caption: str = ""):
    return upload_carousel(image_paths, caption=caption)


def post_as_reel(image_paths: list[str], caption: str = ""):
    video_dir = Path("output/reels")
    video_dir.mkdir(parents=True, exist_ok=True)
    video_path = str(video_dir / "reel.mp4")

    music = get_selected_music()
    music_type = (music or {}).get("id", "synthetic")
    generate_audio = music_type == "synthetic"
    audio_path = music.get("url") if music_type == "url" and music.get("url") else None

    print(f"Creating reel video from {len(image_paths)} slides (music: {music_type})...")
    images_to_video(image_paths, video_path, audio_path=audio_path, generate_audio=generate_audio)
    print(f"Reel video saved: {video_path}")

    return upload_reel(video_path, caption=caption)


def _cleanup_outputs(output_urls: list[str]) -> None:
    removed_dirs: set[str] = set()
    for path in output_urls:
        try:
            if os.path.isfile(path):
                os.remove(path)
                parent = os.path.dirname(path)
                if parent and parent not in removed_dirs and os.path.isdir(parent):
                    if not os.listdir(parent):
                        os.rmdir(parent)
                        removed_dirs.add(parent)
        except OSError as exc:
            print(f"  [cleanup] Could not remove {path}: {exc}")
    print(f"  [cleanup] Removed {len(output_urls)} local slide files")


def post_generated_outputs(
    output_paths: list[str],
    caption: str = "",
    story_title: str = "",
):
    if not output_paths:
        print("No generated output image paths to post.")
        return None

    if not has_instagram_api_config():
        print("No Zernio API key configured. Add ZERNIO_API_KEY to .env.")
        return None

    cfg = get_config()
    as_reel = cfg.get("post_as_reel", True)

    try:
        if as_reel:
            print(f"Uploading {len(output_paths)} images as Instagram Reel...")
            result = post_as_reel(output_paths, caption=caption)
            print("Instagram Reel upload complete.")
        else:
            print(f"Uploading {len(output_paths)} images to Instagram...")
            result = post_to_instagram(output_paths, caption=caption)
            print("Instagram upload complete.")
        _cleanup_outputs(output_paths)
        if result:
            append_log({
                "title": story_title or caption[:60],
                "status": result.get("status", "posted"),
                "post_id": result.get("post_id", ""),
                "type": "reel" if as_reel else "carousel",
                "provider": result.get("provider", "zernio_api"),
            })
        return result
    except ValueError as exc:
        print(f"Instagram upload skipped: {exc}")
        return None
    except Exception as exc:
        print(f"Instagram upload failed: {exc}")
        return None
