# author: sawyer-shi

"""Seedream 模型能力表与尺寸校验工具。

不同 Seedream 模型对请求参数的支持差异较大（参考 v0.0.4 API 文档），
本模块集中维护这些差异，供各 tool 共享，避免在每个 tool 里硬编码 model ID 字符串。
"""

# 模型 ID 常量
MODEL_SEEDREAM_5_PRO = "doubao-seedream-5-0-pro-260628"
MODEL_SEEDREAM_5_LITE = "doubao-seedream-5-0-260128"
MODEL_SEEDREAM_4_5 = "doubao-seedream-4-5-251128"
MODEL_SEEDREAM_4_0 = "doubao-seedream-4-0-250828"

DEFAULT_MODEL = MODEL_SEEDREAM_4_5

# 单张参考图上传大小上限（新 API 已统一放宽到 30MB）
MAX_INPUT_IMAGE_BYTES = 30 * 1024 * 1024


MODEL_CAPS = {
    MODEL_SEEDREAM_5_PRO: {
        "label": "Seedream 5.0 Pro",
        "supports_sequential": False,   # 不支持 sequential_image_generation*
        "supports_stream": False,        # 不支持 stream 字段，传参会报错
        "supports_tools": False,         # 不支持 tools / web_search
        "supports_output_format": True,  # 支持 output_format (png/jpeg)
        "supports_optimize_prompt_fast": False,
        "max_input_images": 10,
        "default_size": "1024x1024",
    },
    MODEL_SEEDREAM_5_LITE: {
        "label": "Seedream 5.0 Lite",
        "supports_sequential": True,
        "supports_stream": True,
        "supports_tools": True,          # 独占 web_search
        "supports_output_format": True,
        "supports_optimize_prompt_fast": False,
        "max_input_images": 14,
        "default_size": "2048x2048",
    },
    MODEL_SEEDREAM_4_5: {
        "label": "Seedream 4.5",
        "supports_sequential": True,
        "supports_stream": True,
        "supports_tools": False,
        "supports_output_format": False,
        "supports_optimize_prompt_fast": False,
        "max_input_images": 14,
        "default_size": "2048x2048",
    },
    MODEL_SEEDREAM_4_0: {
        "label": "Seedream 4.0",
        "supports_sequential": True,
        "supports_stream": True,
        "supports_tools": False,
        "supports_output_format": False,
        "supports_optimize_prompt_fast": True,  # 独占 fast 模式
        "max_input_images": 14,
        "default_size": "2048x2048",
    },
}


def get_caps(model: str) -> dict:
    if model not in MODEL_CAPS:
        raise ValueError(f"未知模型 ID: {model}")
    return MODEL_CAPS[model]


# value 为 None 表示该尺寸所有模型都支持；否则为支持的模型 ID 集合。
SIZE_TO_MODELS = {
    # ===== 通用 2K（4 个模型都支持） =====
    "2048x2048": None,
    "2304x1728": None,
    "1728x2304": None,
    "2848x1600": None,
    "1600x2848": None,
    "2496x1664": None,
    "1664x2496": None,
    "3136x1344": None,
    # ===== 通用 4K（5.0 Lite / 4.5 / 4.0） =====
    "4096x4096": {MODEL_SEEDREAM_5_LITE, MODEL_SEEDREAM_4_5, MODEL_SEEDREAM_4_0},
    "4704x3520": {MODEL_SEEDREAM_5_LITE, MODEL_SEEDREAM_4_5, MODEL_SEEDREAM_4_0},
    "3520x4704": {MODEL_SEEDREAM_5_LITE, MODEL_SEEDREAM_4_5, MODEL_SEEDREAM_4_0},
    "5504x3040": {MODEL_SEEDREAM_5_LITE, MODEL_SEEDREAM_4_5, MODEL_SEEDREAM_4_0},
    "3040x5504": {MODEL_SEEDREAM_5_LITE, MODEL_SEEDREAM_4_5, MODEL_SEEDREAM_4_0},
    "4992x3328": {MODEL_SEEDREAM_5_LITE, MODEL_SEEDREAM_4_5, MODEL_SEEDREAM_4_0},
    "3328x4992": {MODEL_SEEDREAM_5_LITE, MODEL_SEEDREAM_4_5, MODEL_SEEDREAM_4_0},
    "6240x2656": {MODEL_SEEDREAM_5_LITE, MODEL_SEEDREAM_4_5, MODEL_SEEDREAM_4_0},
    # ===== 5.0 Lite 3K 独占 =====
    "3072x3072": {MODEL_SEEDREAM_5_LITE},
    "3456x2592": {MODEL_SEEDREAM_5_LITE},
    "2592x3456": {MODEL_SEEDREAM_5_LITE},
    "4096x2304": {MODEL_SEEDREAM_5_LITE},
    "2304x4096": {MODEL_SEEDREAM_5_LITE},
    "3744x2496": {MODEL_SEEDREAM_5_LITE},
    "2496x3744": {MODEL_SEEDREAM_5_LITE},
    "4704x2016": {MODEL_SEEDREAM_5_LITE},
    # ===== 5.0 Pro 专属 2K（与通用 2K 同档但像素不同） =====
    "2368x1776": {MODEL_SEEDREAM_5_PRO},
    "1776x2368": {MODEL_SEEDREAM_5_PRO},
    "2816x1584": {MODEL_SEEDREAM_5_PRO},
    "1584x2816": {MODEL_SEEDREAM_5_PRO},
    # ===== 1K - 1:1 / 4:3 / 3:4 在 Pro 与 4.0 像素值相同 =====
    "1024x1024": {MODEL_SEEDREAM_5_PRO, MODEL_SEEDREAM_4_0},
    "1152x864":  {MODEL_SEEDREAM_5_PRO, MODEL_SEEDREAM_4_0},
    "864x1152":  {MODEL_SEEDREAM_5_PRO, MODEL_SEEDREAM_4_0},
    # ===== 5.0 Pro 1K 独占 =====
    "1424x800": {MODEL_SEEDREAM_5_PRO},
    "800x1424": {MODEL_SEEDREAM_5_PRO},
    "1568x672": {MODEL_SEEDREAM_5_PRO},
    # ===== 4.0 1K 独占 =====
    "1280x720": {MODEL_SEEDREAM_4_0},
    "720x1280": {MODEL_SEEDREAM_4_0},
    "1512x648": {MODEL_SEEDREAM_4_0},
}


def assert_size_for_model(size: str, model: str) -> None:
    """校验所选尺寸在所选模型下是否合法，不合法抛 ValueError。"""
    allowed = SIZE_TO_MODELS.get(size)
    if allowed is None:
        return
    if model not in allowed:
        label = MODEL_CAPS.get(model, {}).get("label", model)
        raise ValueError(
            f"尺寸 {size} 不支持模型 {label}，请参考下拉项中的模型标签重新选择尺寸"
        )


def assert_input_images_count(count: int, model: str) -> None:
    """校验多图输入数量是否超出模型上限。"""
    caps = get_caps(model)
    if count > caps["max_input_images"]:
        raise ValueError(
            f"模型 {caps['label']} 最多支持 {caps['max_input_images']} 张参考图，"
            f"当前传入 {count} 张"
        )
