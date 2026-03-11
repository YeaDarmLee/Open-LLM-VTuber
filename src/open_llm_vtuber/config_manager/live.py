from pydantic import Field
from typing import Dict, ClassVar, List, Optional
from .i18n import I18nMixin, Description


class BiliBiliLiveConfig(I18nMixin):
    """Configuration for BiliBili Live platform."""

    room_ids: List[int] = Field([], alias="room_ids")
    sessdata: str = Field("", alias="sessdata")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "room_ids": Description(
            en="List of BiliBili live room IDs to monitor", zh="要监控의 B站直播间ID列表"
        ),
        "sessdata": Description(
            en="SESSDATA cookie value for authenticated requests (optional)",
            zh="用于认证请求의 SESSDATA cookie值（可选）",
        ),
    }


class ChzzkLiveConfig(I18nMixin):
    """Configuration for Chzzk Live platform."""

    channel_id: str = Field("", alias="channel_id")
    use_official_api: bool = Field(True, alias="use_official_api")
    access_token: Optional[str] = Field(None, alias="access_token")
    refresh_token: Optional[str] = Field(None, alias="refresh_token")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "channel_id": Description(
            en="Chzzk Channel ID to monitor", zh="要监控의 치지직 채널 ID"
        ),
        "use_official_api": Description(
            en="Whether to use the official Chzzk API (requires authentication)",
            zh="是否使用치지직 공식 API (인증 필요)",
        ),
        "access_token": Description(
            en="Official API Access Token", zh="공식 API 액세스 토큰"
        ),
        "refresh_token": Description(
            en="Official API Refresh Token", zh="공식 API 리프레시 토큰"
        ),
    }


class LiveConfig(I18nMixin):
    """Configuration for live streaming platforms integration."""

    bilibili_live: BiliBiliLiveConfig = Field(
        BiliBiliLiveConfig(), alias="bilibili_live"
    )
    chzzk_live: ChzzkLiveConfig = Field(ChzzkLiveConfig(), alias="chzzk_live")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "bilibili_live": Description(
            en="Configuration for BiliBili Live platform", zh="B站直播平台配置"
        ),
        "chzzk_live": Description(
            en="Configuration for Chzzk Live platform", zh="치지직 라이브 플랫폼 설정"
        ),
    }
