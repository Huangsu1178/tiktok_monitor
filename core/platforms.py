"""
Platform helpers for TikTok / Douyin compatibility.
"""
from __future__ import annotations

from urllib.parse import urlparse


SUPPORTED_PLATFORMS = {
    "tiktok": {
        "label": "TikTok",
        "domains": ("www.tiktok.com", "tiktok.com", "m.tiktok.com"),
    },
    "douyin": {
        "label": "抖音",
        "domains": ("www.douyin.com", "douyin.com", "v.douyin.com"),
    },
}


def normalize_platform(platform: str | None) -> str:
    value = (platform or "tiktok").strip().lower()
    return value if value in SUPPORTED_PLATFORMS else "tiktok"


def platform_label(platform: str) -> str:
    return SUPPORTED_PLATFORMS.get(normalize_platform(platform), SUPPORTED_PLATFORMS["tiktok"])["label"]


def infer_platform_from_input(raw: str) -> str:
    value = (raw or "").strip().lower()
    if "douyin.com" in value or "v.douyin.com" in value or "抖音" in value:
        return "douyin"
    return "tiktok"


def normalize_influencer_input(raw: str, platform: str) -> tuple[str, str]:
    platform = normalize_platform(platform)
    value = (raw or "").strip()
    if not value:
        return "", ""

    if value.startswith("http://") or value.startswith("https://"):
        parsed = urlparse(value)
        path = parsed.path.strip("/")
        if platform == "tiktok":
            username = path.split("@")[-1].split("/")[0] if "@" in path else path.split("/")[0]
            return username.strip("@"), value

        host = (parsed.netloc or "").lower()
        parts = [part for part in path.split("/") if part]
        if "douyin.com" in host and len(parts) >= 2 and parts[0] == "user":
            return parts[-1], value
        if parts:
            return parts[-1], value
        return "", value

    cleaned = value.strip("@")
    if platform == "tiktok":
        return cleaned, f"https://www.tiktok.com/@{cleaned}"
    return "", ""


def format_account_identity(platform: str, username: str, profile_url: str = "") -> str:
    platform = normalize_platform(platform)
    username = (username or "").strip()
    profile_url = (profile_url or "").strip()
    if platform == "douyin":
        return profile_url or username
    return f"@{username}" if username else profile_url


def build_video_url(platform: str, username: str, video_id: str) -> str:
    platform = normalize_platform(platform)
    if platform == "douyin":
        return f"https://www.douyin.com/video/{video_id}"
    return f"https://www.tiktok.com/@{username}/video/{video_id}"
