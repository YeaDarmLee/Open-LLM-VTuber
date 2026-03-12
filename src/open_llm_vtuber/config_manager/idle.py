from pydantic import Field
from typing import Dict, ClassVar
from .i18n import I18nMixin, Description

class IdleTalkConfig(I18nMixin):
    """Configuration for autonomous idle talking."""

    enabled: bool = Field(True, alias="enabled")
    min_delay: int = Field(40, alias="min_delay")
    max_delay: int = Field(90, alias="max_delay")
    cooldown: int = Field(120, alias="cooldown")
    probability: float = Field(0.7, alias="probability")

    DESCRIPTIONS: ClassVar[Dict[str, Description]] = {
        "enabled": Description(en="Enable idle talk system", zh="启用空闲聊天系统"),
        "min_delay": Description(
            en="Minimum delay in seconds before triggering idle talk",
            zh="触发空闲聊天的最小延迟（秒）",
        ),
        "max_delay": Description(
            en="Maximum delay in seconds before triggering idle talk",
            zh="触发空闲聊天的最大延迟（秒）",
        ),
        "cooldown": Description(
            en="Cooldown in seconds after an idle talk before another can happen",
            zh="空闲聊天后的冷却时间（秒）",
        ),
        "probability": Description(
            en="Probability (0.0 to 1.0) of triggering idle talk",
            zh="触发空闲聊天的概率 (0.0 到 1.0)",
        ),
    }
