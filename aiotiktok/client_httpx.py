import httpx
import json
import re
from typing import Any, Callable, Dict
from urllib.parse import urljoin
from .exceptions import UrlUnavailable, VideoUnavailable
from .types import Aweme

class TikTokClientHttpx:
    def __init__(
        self,
        host: str | None = None,
        json_loads: Callable[..., dict[str, Any]] = json.loads,
    ):
        self.host = (
            "https://api22-normal-c-alisg.tiktokv.com/" if host is None else host
        )
        self.json_loads = json_loads
        self.client = httpx.AsyncClient()

    async def close(self) -> None:
        await self.client.aclose()

    async def _make_request(
        self, method: str, endpoint: str, **kwargs: dict[str, Any]
    ) -> Dict[str, Any]:
        url = urljoin(self.host, endpoint)
        response = await self.client.request(method, url, **kwargs)
        response.raise_for_status()
        return self.json_loads(response.text)

    async def get_video_id(self, video_url: str) -> str:
        response = await self.client.get(video_url)
        web_url = str(response.url)
        if (
            web_url == "https://tiktok.com"
            or "video" not in web_url
            and "photo" not in web_url
        ):
            raise UrlUnavailable(video_url)
        video_id_match = re.findall("/(?:photo|video)/(\d+)", web_url)
        if not video_id_match:
            raise UrlUnavailable(video_url)
        return video_id_match[0]

    async def get_video_data(
        self, video_url: str | None = None, video_id: str | None = None
    ) -> Aweme:
        if not video_url and not video_id:
            raise ValueError("You must provide either a video_url or video_id")
        if not video_id and video_url:
            video_id = await self.get_video_id(video_url)
        params = {
            "iid": "7318518857994389254",
            "device_id": "7318517321748022790",
            "channel": "googleplay",
            "app_name": "musical_ly",
            "version_code": "300904",
            "device_platform": "android",
            "device_type": "ASUS_Z01QD",
            "os_version": "9",
            "aweme_id": video_id,
        }
        data = await self._make_request("OPTIONS", "aweme/v1/feed/", params=params)
        for aweme in data["aweme_list"]:
            print(f'awid is {aweme["aweme_id"]}')
            if aweme["aweme_id"] == video_id:
                aweme_list = aweme["video"]["play_addr"]["url_list"][0]
                cover_addr = aweme["video"]["cover"]["url_list"][0]
                return Aweme(aweme_list, cover_addr)
        raise VideoUnavailable(video_id)