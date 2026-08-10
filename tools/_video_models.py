# author: sawyer-shi

"""Seedance 视频模型能力表与参数规整工具。

不同 Seedance 模型对请求参数的支持差异较大（参考 v0.0.7 API 文档），
本模块集中维护这些差异，供各视频 tool 共享，避免在每个 tool 里硬编码
模型 ID 字符串与判定分支。图像模型的能力表见 `_capabilities.py`。
"""

from typing import Any

# ===== 模型 ID 常量 =====
MODEL_SEEDANCE_2_5 = "doubao-seedance-2-5-260628"
MODEL_SEEDANCE_2_0 = "doubao-seedance-2-0-260128"
MODEL_SEEDANCE_2_0_FAST = "doubao-seedance-2-0-fast-260128"
MODEL_SEEDANCE_2_0_MINI = "doubao-seedance-2-0-mini-260615"
MODEL_SEEDANCE_1_5_PRO = "doubao-seedance-1-5-pro-251215"
MODEL_SEEDANCE_1_0_PRO = "doubao-seedance-1-0-pro-250528"
MODEL_SEEDANCE_1_0_PRO_FAST = "doubao-seedance-1-0-pro-fast-251015"

DEFAULT_VIDEO_MODEL = MODEL_SEEDANCE_1_5_PRO

# 历史别名 -> 最新 Model ID
MODEL_ALIASES = {
    "doubao-seedance-2-0-fast-250428": MODEL_SEEDANCE_2_0_FAST,
}

# 各家族能力表。resolution 列表中未出现的取值会被回退到 default_resolution。
VIDEO_MODEL_CAPS: dict[str, dict[str, Any]] = {
    "2.5": {
        "family": "2.5",
        "supports_camera_fixed": False,
        "supports_service_tier": False,      # 不支持 flex，且不下发 service_tier
        "supports_bitrate_mode": False,      # 2.5 文档未列出该参数，不下发
        "supports_output_format": True,      # 独占 mp4 / mov
        "supports_priority": True,           # 2.5 / 2.0 系列
        "supports_web_search": True,         # 2.5 / 2.0 系列
        "supports_generate_audio": True,
        "supports_draft": False,
        "supports_return_last_frame": True,
        "supports_duration_auto": True,      # duration = -1 智能选择
        "resolutions": ("480p", "720p"),
        "default_resolution": "720p",
        "duration_range": (4, 30),
        "max_reference_images": 30,
        "max_reference_videos": 10,
        "max_reference_audios": 10,
        "supports_audio_only": True,         # 可仅传入音频
    },
    "2.0": {
        "family": "2.0",
        "supports_camera_fixed": False,
        "supports_service_tier": False,
        "supports_bitrate_mode": True,       # 2.0 系列独占
        "supports_output_format": False,
        "supports_priority": True,
        "supports_web_search": True,
        "supports_generate_audio": True,
        "supports_draft": False,
        "supports_return_last_frame": True,
        "supports_duration_auto": True,
        # 注：完整版 Seedance 2.0 支持 1080p/4k，但 fast/mini 仅 480p/720p；
        # 沿用历史行为，2.0 系列统一将 1080p 回退到 720p。
        "resolutions": ("480p", "720p"),
        "default_resolution": "720p",
        "duration_range": (4, 15),
        "max_reference_images": 9,
        "max_reference_videos": 3,
        "max_reference_audios": 3,
        "supports_audio_only": False,
    },
    "1.5": {
        "family": "1.5",
        "supports_camera_fixed": True,
        "supports_service_tier": True,       # 支持 default / flex
        "supports_bitrate_mode": False,
        "supports_output_format": False,
        "supports_priority": False,
        "supports_web_search": False,
        "supports_generate_audio": True,
        "supports_draft": True,              # 独占样片模式
        "supports_return_last_frame": True,
        "supports_duration_auto": True,
        "resolutions": ("480p", "720p", "1080p"),
        "default_resolution": "720p",
        "duration_range": (4, 12),
    },
    "1.0": {
        "family": "1.0",
        "supports_camera_fixed": True,
        "supports_service_tier": True,
        "supports_bitrate_mode": False,
        "supports_output_format": False,
        "supports_priority": False,
        "supports_web_search": False,
        "supports_generate_audio": False,
        "supports_draft": False,
        "supports_return_last_frame": True,
        "supports_duration_auto": False,     # 不支持 duration = -1
        "resolutions": ("480p", "720p", "1080p"),
        "default_resolution": "1080p",
        "duration_range": (2, 12),
    },
    "1.0_fast": {
        "family": "1.0_fast",
        "supports_camera_fixed": True,
        "supports_service_tier": True,
        "supports_bitrate_mode": False,
        "supports_output_format": False,
        "supports_priority": False,
        "supports_web_search": False,
        "supports_generate_audio": False,
        "supports_draft": False,
        "supports_return_last_frame": True,
        "supports_duration_auto": False,
        "resolutions": ("480p", "720p", "1080p"),
        "default_resolution": "1080p",
        "duration_range": (2, 12),
    },
}


def resolve_model(model: str) -> str:
    """应用历史别名，返回最新 Model ID。"""
    return MODEL_ALIASES.get(model, model)


def _family_of(model: str) -> str:
    m = model.lower()
    if "seedance-2-5" in m:
        return "2.5"
    if "seedance-2-0" in m:
        return "2.0"
    if "seedance-1-5-pro" in m:
        return "1.5"
    if "seedance-1-0-pro-fast" in m:
        return "1.0_fast"
    if "seedance-1-0-pro" in m:
        return "1.0"
    return "1.0"


def get_video_caps(model: str) -> dict[str, Any]:
    """按模型 ID 返回能力配置，未知模型回退到 1.0 规则。"""
    return VIDEO_MODEL_CAPS[_family_of(model)]


def is_seedance_2_5(model: str) -> bool:
    return "seedance-2-5" in model.lower()


def is_seedance_2_0_series(model: str) -> bool:
    return "seedance-2-0" in model.lower()


def is_seedance_2_series(model: str) -> bool:
    """Seedance 2.5 + 2.0 系列。"""
    return is_seedance_2_5(model) or is_seedance_2_0_series(model)


def is_seedance_1_5_pro(model: str) -> bool:
    return "seedance-1-5-pro" in model.lower()


def clamp_seed(seed: int) -> int:
    if seed < -1:
        return -1
    if seed > 4294967295:
        return 4294967295
    return seed


def normalize_core_params(
    model: str,
    *,
    duration: int,
    resolution: str,
    seed: int,
    draft: bool,
    return_last_frame: bool,
) -> dict[str, Any]:
    """规整各模型通用的核心参数：duration / resolution / seed / draft / return_last_frame。"""
    caps = get_video_caps(model)

    if duration == -1:
        duration = -1 if caps["supports_duration_auto"] else 5
    else:
        lo, hi = caps["duration_range"]
        duration = max(lo, min(hi, int(duration)))

    if resolution not in caps["resolutions"]:
        resolution = caps["default_resolution"]

    if draft and not caps["supports_draft"]:
        draft = False
    if draft and return_last_frame:
        return_last_frame = False

    return {
        "duration": duration,
        "resolution": resolution,
        "seed": clamp_seed(seed),
        "draft": draft,
        "return_last_frame": return_last_frame,
    }


def tier_payload(
    model: str,
    *,
    camera_fixed: bool,
    service_tier: str,
    bitrate_mode: str,
) -> dict[str, Any]:
    """按模型拼装 camera_fixed / service_tier / bitrate_mode。

    - 1.5 / 1.0 系列：下发 camera_fixed + service_tier
    - 2.0 系列：下发 bitrate_mode
    - 2.5：三者均不下发
    """
    caps = get_video_caps(model)
    payload: dict[str, Any] = {}
    if caps["supports_camera_fixed"]:
        payload["camera_fixed"] = camera_fixed
        payload["service_tier"] = service_tier
    elif caps["supports_bitrate_mode"]:
        payload["bitrate_mode"] = bitrate_mode
    return payload


def extra_payload(
    model: str,
    *,
    output_format: str,
    priority: int,
    web_search: bool,
) -> dict[str, Any]:
    """按模型拼装 2.5/2.0 系列新增参数：output_format / priority / tools(web_search)。"""
    caps = get_video_caps(model)
    payload: dict[str, Any] = {}
    if caps["supports_output_format"] and output_format:
        payload["output_format"] = output_format
    if caps["supports_priority"]:
        payload["priority"] = priority
    if caps["supports_web_search"] and web_search:
        payload["tools"] = [{"type": "web_search"}]
    return payload
