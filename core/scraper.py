"""
Multi-platform scraper module for TikTok / Douyin.
"""
import asyncio
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

sys.path.append('/opt/.manus/.sandbox-runtime')

try:
    from data_api import ApiClient
    MANUS_API_AVAILABLE = True
except ImportError:
    MANUS_API_AVAILABLE = False

from core.platforms import build_video_url, normalize_platform, platform_label


def format_count(count_str: str) -> int:
    if not count_str:
        return 0
    text = str(count_str).strip().upper().replace(",", "")
    try:
        if "K" in text:
            return int(float(text.replace("K", "")) * 1_000)
        if "M" in text:
            return int(float(text.replace("M", "")) * 1_000_000)
        if "B" in text:
            return int(float(text.replace("B", "")) * 1_000_000_000)
        if "W" in text:
            return int(float(text.replace("W", "")) * 10_000)
        return int(float(text))
    except (ValueError, TypeError):
        return 0


class MultiPlatformScraper:
    """TikTok / Douyin scraper with platform-aware URL handling."""

    def __init__(self, proxy_url: str = "", headless: bool = True):
        self.proxy_url = proxy_url
        self.headless = headless
        self._use_api = MANUS_API_AVAILABLE
        self._api_client = ApiClient() if MANUS_API_AVAILABLE else None

    def get_user_info(self, influencer: Dict[str, Any]) -> Dict[str, Any]:
        platform = normalize_platform(influencer.get("platform"))
        username = influencer.get("username", "").strip("@")
        profile_url = influencer.get("profile_url", "")

        if platform == "tiktok" and self._use_api:
            try:
                response = self._api_client.call_api(
                    "Tiktok/get_user_info",
                    query={"uniqueId": username},
                )
                parsed = self._parse_tiktok_user_info_api(response, username)
                if parsed:
                    return parsed
            except BaseException as exc:
                print(f"[Scraper] TikTok API user info failed: {exc}")

        try:
            return asyncio.run(self._get_user_info_playwright(platform, username, profile_url))
        except BaseException as exc:
            print(f"[Scraper] Playwright user info failed before coroutine completed: {exc}")
            return {"username": username, "profile_url": profile_url or self._default_profile_url(platform, username)}

    def get_user_videos(self, influencer: Dict[str, Any], max_count: int = 20) -> List[Dict[str, Any]]:
        platform = normalize_platform(influencer.get("platform"))
        username = influencer.get("username", "").strip("@")
        profile_url = influencer.get("profile_url", "")

        print(f"[Scraper] Fetching {platform_label(platform)} videos for {username}")
        if platform != "douyin":
            try:
                return self._get_user_videos_ytdlp(platform, username, profile_url, max_count)
            except BaseException as exc:
                print(f"[Scraper] yt-dlp mode failed: {exc}")

        try:
            return asyncio.run(self._get_user_videos_playwright(platform, username, profile_url, max_count))
        except BaseException as exc:
            print(f"[Scraper] Playwright videos failed before coroutine completed: {exc}")
            return []

    def _parse_tiktok_user_info_api(self, response: dict, username: str) -> Dict[str, Any]:
        if not response:
            return {}
        user_info = response.get("userInfo", {})
        user = user_info.get("user", {})
        stats = user_info.get("stats", {})
        return {
            "username": user.get("uniqueId", username),
            "display_name": user.get("nickname", ""),
            "bio": user.get("signature", ""),
            "avatar_url": user.get("avatarMedium", ""),
            "follower_count": stats.get("followerCount", 0),
            "following_count": stats.get("followingCount", 0),
            "video_count": stats.get("videoCount", 0),
            "profile_url": f"https://www.tiktok.com/@{username}",
        }

    async def _get_user_info_playwright(self, platform: str, username: str, profile_url: str) -> Dict[str, Any]:
        target_url = profile_url or self._default_profile_url(platform, username)
        fallback = {"username": username, "profile_url": target_url}
        browser = None
        context = None
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser_args = {}
                if self.proxy_url:
                    browser_args["proxy"] = {"server": self.proxy_url}

                browser = await p.chromium.launch(headless=self.headless, **browser_args)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800},
                    locale="zh-CN" if platform == "douyin" else "en-US",
                )
                page = await context.new_page()
                await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)

                info = dict(fallback)
                selectors = self._user_info_selectors(platform)

                for key, selector in selectors.items():
                    try:
                        text = await page.locator(selector).first.inner_text()
                        if key == "follower_count":
                            info[key] = format_count(text)
                        else:
                            info[key] = text
                    except Exception:
                        continue

                return info
        except BaseException as exc:
            print(f"[Scraper] Playwright user info failed: {exc}")
            return fallback
        finally:
            if context is not None:
                try:
                    await context.close()
                except Exception:
                    pass
            if browser is not None:
                try:
                    await browser.close()
                except Exception:
                    pass

    def _get_user_videos_ytdlp(self, platform: str, username: str, profile_url: str, max_count: int) -> List[Dict[str, Any]]:
        import yt_dlp

        url = profile_url or self._default_profile_url(platform, username)
        videos: List[Dict[str, Any]] = []
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,
            "playlistend": max_count,
        }
        if self.proxy_url:
            ydl_opts["proxy"] = self.proxy_url

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return []
            entries = info.get("entries", [])
            if not entries and "id" in info:
                entries = [info]

            for entry in entries[:max_count]:
                if not entry:
                    continue
                video_id = entry.get("id", "")
                if not video_id:
                    continue
                videos.append(
                    {
                        "platform": platform,
                        "video_id": video_id,
                        "title": (entry.get("title", "") or "")[:100],
                        "description": entry.get("description", "") or "",
                        "video_url": entry.get("webpage_url", "") or build_video_url(platform, username, video_id),
                        "thumbnail_url": entry.get("thumbnail", ""),
                        "play_count": entry.get("view_count", 0) or 0,
                        "like_count": entry.get("like_count", 0) or 0,
                        "comment_count": entry.get("comment_count", 0) or 0,
                        "share_count": entry.get("repost_count", 0) or 0,
                        "duration": entry.get("duration", 0) or 0,
                        "hashtags": "",
                        "music_name": entry.get("artist", "") or entry.get("track", "") or "",
                        "published_at": datetime.fromtimestamp(entry.get("timestamp", 0)).strftime("%Y-%m-%d %H:%M:%S")
                        if entry.get("timestamp")
                        else "",
                    }
                )
        return videos

    async def _get_user_videos_playwright(self, platform: str, username: str, profile_url: str, max_count: int) -> List[Dict[str, Any]]:
        target_url = profile_url or self._default_profile_url(platform, username)
        videos: List[Dict[str, Any]] = []
        browser = None
        context = None
        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser_args = {}
                if self.proxy_url:
                    browser_args["proxy"] = {"server": self.proxy_url}

                browser = await p.chromium.launch(headless=self.headless, **browser_args)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1280, "height": 800},
                    locale="zh-CN" if platform == "douyin" else "en-US",
                )
                page = await context.new_page()
                await page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(4000)

                if platform == "douyin":
                    for _ in range(3):
                        await page.mouse.wheel(0, 1800)
                        await page.wait_for_timeout(1200)

                selectors = self._video_card_selectors(platform)
                card_selector = selectors["card"]
                cards = await page.locator(card_selector).all()

                for card in cards[:max_count]:
                    try:
                        href = await card.get_attribute("href")
                        if not href:
                            try:
                                href = await card.locator("a").first.get_attribute("href")
                            except Exception:
                                href = ""
                        if not href:
                            continue
                        video_id = self._extract_video_id(href)
                        if not video_id:
                            continue

                        play_text = ""
                        try:
                            play_text = await card.locator(selectors["play"]).first.inner_text()
                        except Exception:
                            pass

                        videos.append(
                            {
                                "platform": platform,
                                "video_id": video_id,
                                "title": "",
                                "description": "",
                                "video_url": href if href.startswith("http") else self._absolute_url(platform, href),
                                "thumbnail_url": "",
                                "play_count": format_count(play_text),
                                "like_count": 0,
                                "comment_count": 0,
                                "share_count": 0,
                                "duration": 0,
                                "hashtags": "",
                                "music_name": "",
                                "published_at": "",
                            }
                        )
                    except Exception as exc:
                        print(f"[Scraper] DOM parse failed: {exc}")

        except BaseException as exc:
            print(f"[Scraper] Playwright videos failed: {exc}")
        finally:
            if context is not None:
                try:
                    await context.close()
                except Exception:
                    pass
            if browser is not None:
                try:
                    await browser.close()
                except Exception:
                    pass
        return videos

    def download_video_no_watermark(self, video_url: str, output_dir: str, filename: str = "") -> Optional[str]:
        try:
            import yt_dlp

            os.makedirs(output_dir, exist_ok=True)
            if not filename:
                video_id = self._extract_video_id(video_url) or "video"
                filename = f"video_{video_id}"

            output_path = os.path.join(output_dir, f"{filename}.%(ext)s")
            ydl_opts = {
                "outtmpl": output_path,
                "format": "bestvideo+bestaudio/best",
                "quiet": True,
                "no_warnings": True,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            }
            if self.proxy_url:
                ydl_opts["proxy"] = self.proxy_url

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                ext = info.get("ext", "mp4")
                final_path = os.path.join(output_dir, f"{filename}.{ext}")
                if os.path.exists(final_path):
                    return final_path

            for file_name in os.listdir(output_dir):
                if file_name.startswith(filename):
                    return os.path.join(output_dir, file_name)
        except Exception as exc:
            print(f"[Scraper] Video download failed: {exc}")
        return None

    def _default_profile_url(self, platform: str, username: str) -> str:
        if platform == "douyin":
            return f"https://www.douyin.com/user/{username}"
        return f"https://www.tiktok.com/@{username}"

    def _absolute_url(self, platform: str, href: str) -> str:
        if href.startswith("http"):
            return href
        if platform == "douyin":
            return f"https://www.douyin.com{href}"
        return f"https://www.tiktok.com{href}"

    def _extract_video_id(self, url: str) -> str:
        text = (url or "").split("?")[0].rstrip("/")
        if "/video/" in text:
            return text.split("/video/")[-1]
        if "modal_id=" in (url or ""):
            return (url or "").split("modal_id=")[-1].split("&")[0]
        return text.split("/")[-1]

    def _video_card_selectors(self, platform: str) -> Dict[str, str]:
        if platform == "douyin":
            return {
                "card": "a[href*='/video/'], a[href*='modal_id=']",
                "play": "[data-e2e='video-views'], span",
            }
        return {
            "card": "a[href*='/video/'], [data-e2e='user-post-item']",
            "play": "[data-e2e='video-views'], span",
        }

    def _user_info_selectors(self, platform: str) -> Dict[str, str]:
        if platform == "douyin":
            return {
                "display_name": "h1, [data-e2e='user-title']",
                "bio": "[data-e2e='user-bio'], .TUXText",
                "follower_count": "strong, [data-e2e='followers-count']",
            }
        return {
            "display_name": "[data-e2e='user-title']",
            "bio": "[data-e2e='user-bio']",
            "follower_count": "[data-e2e='followers-count']",
        }


class TikTokScraper(MultiPlatformScraper):
    """Backward-compatible alias."""


class FetchTask:
    """Single influencer fetch task."""

    def __init__(self, scraper: MultiPlatformScraper):
        self.scraper = scraper

    def run(self, influencer: dict, max_videos: int = 20) -> dict:
        from data.database import add_fetch_log, save_video, update_influencer_profile

        username = influencer["username"]
        influencer_id = influencer["id"]
        platform = normalize_platform(influencer.get("platform"))
        started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"[Task] Start fetching {platform_label(platform)} creator {username}")

        try:
            user_info = self.scraper.get_user_info(influencer)
            if user_info:
                update_influencer_profile(
                    influencer_id,
                    {
                        "display_name": user_info.get("display_name", ""),
                        "follower_count": user_info.get("follower_count", 0),
                        "following_count": user_info.get("following_count", 0),
                        "video_count": user_info.get("video_count", 0),
                        "bio": user_info.get("bio", ""),
                        "avatar_url": user_info.get("avatar_url", ""),
                        "profile_url": user_info.get("profile_url", influencer.get("profile_url", "")),
                        "last_fetched_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    },
                )

            videos = self.scraper.get_user_videos(influencer, max_videos)
            videos_found = len(videos)
            videos_new = 0
            for video in videos:
                is_new = save_video(influencer_id, video)
                if is_new:
                    videos_new += 1

            finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            add_fetch_log(
                influencer_id=influencer_id,
                status="success",
                message=f"成功抓取 {videos_found} 个视频，其中 {videos_new} 个为新视频",
                videos_found=videos_found,
                videos_new=videos_new,
                started_at=started_at,
                finished_at=finished_at,
            )
            return {
                "status": "success",
                "platform": platform,
                "username": username,
                "videos_found": videos_found,
                "videos_new": videos_new,
            }
        except BaseException as exc:
            finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            add_fetch_log(
                influencer_id=influencer_id,
                status="error",
                message=str(exc),
                started_at=started_at,
                finished_at=finished_at,
            )
            print(f"[Task] Fetch failed for {username}: {exc}")
            return {"status": "error", "platform": platform, "username": username, "error": str(exc)}
