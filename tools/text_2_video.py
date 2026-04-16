# author: sawyer-shi

import json
import logging
from collections.abc import Generator
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

logger = logging.getLogger(__name__)

SEEDANCE_2_MODELS = {
    "doubao-seedance-2-0-260128",
    "doubao-seedance-2-0-fast-260128",
}

MODEL_ALIASES = {
    "doubao-seedance-2-0-fast-250428": "doubao-seedance-2-0-fast-260128",
}


def _is_seedance_2_series(model: str) -> bool:
    normalized = model.lower()
    return normalized in SEEDANCE_2_MODELS or "seedance-2-0" in normalized


def _is_seedance_1_5_pro(model: str) -> bool:
    return "seedance-1-5-pro" in model.lower()


class Text2VideoTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        Volcengine Ark Contents Generations API text-to-video tool.
        """
        logger.info("Starting text-to-video task (Ark)")

        try:
            api_key = self.runtime.credentials.get("api_key")
            if not api_key:
                msg = "❌ API密钥未配置"
                logger.error(msg)
                yield self.create_text_message(msg)
                return

            api_url = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            prompt = tool_parameters.get("prompt", "").strip()
            if not prompt:
                msg = "❌ 请输入提示词"
                logger.warning(msg)
                yield self.create_text_message(msg)
                return

            model = tool_parameters.get("model", "doubao-seedance-1-5-pro-251215")
            model = MODEL_ALIASES.get(model, model)
            resolution = tool_parameters.get("resolution", "720p")
            ratio = tool_parameters.get("ratio", "16:9")
            duration = tool_parameters.get("duration", 5)
            seed = tool_parameters.get("seed", -1)
            camera_fixed = tool_parameters.get("camera_fixed", "false") == "true"
            watermark = tool_parameters.get("watermark", "false") == "true"
            generate_audio = tool_parameters.get("generate_audio", "true") == "true"
            draft = tool_parameters.get("draft", "false") == "true"
            return_last_frame = tool_parameters.get("return_last_frame", "false") == "true"
            service_tier = tool_parameters.get("service_tier", "default")

            if len(prompt) > 500:
                prompt = prompt[:500]

            is_seedance_2 = _is_seedance_2_series(model)
            is_seedance_1_5 = _is_seedance_1_5_pro(model)

            if duration == -1 and not (is_seedance_2 or is_seedance_1_5):
                duration = 5
            elif duration is not None and duration != -1:
                min_duration, max_duration = 2, 12
                if is_seedance_2:
                    min_duration, max_duration = 4, 15
                elif is_seedance_1_5:
                    min_duration, max_duration = 4, 12

                if duration < min_duration:
                    duration = min_duration
                elif duration > max_duration:
                    duration = max_duration

            if is_seedance_2 and resolution == "1080p":
                resolution = "720p"

            if draft and not is_seedance_1_5:
                draft = False

            if draft and return_last_frame:
                return_last_frame = False

            if is_seedance_2 and service_tier == "flex":
                service_tier = "default"

            if seed < -1:
                seed = -1
            elif seed > 4294967295:
                seed = 4294967295

            yield self.create_text_message("🚀 文生视频任务启动中...")
            yield self.create_text_message(f"🤖 使用模型: {model}")
            yield self.create_text_message(
                f"📝 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}"
            )
            yield self.create_text_message(
                f"📐 分辨率: {resolution}, 宽高比: {ratio}"
            )
            yield self.create_text_message("⏳ 正在连接火山方舟 API...")

            payload: dict[str, Any] = {
                "model": model,
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ],
                "resolution": resolution,
                "ratio": ratio,
                "duration": duration,
                "seed": seed,
                "watermark": watermark,
                "generate_audio": generate_audio,
                "draft": draft,
                "return_last_frame": return_last_frame,
            }

            if not is_seedance_2:
                payload["camera_fixed"] = camera_fixed
                payload["service_tier"] = service_tier

            logger.info("Submitting request: %s", json.dumps(payload, ensure_ascii=False))
            yield self.create_text_message("🎬 正在生成视频，请稍候...")

            try:
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=60,
                )
            except requests.exceptions.Timeout:
                msg = "❌ 请求超时，请稍后重试"
                logger.error(msg)
                yield self.create_text_message(msg)
                return
            except requests.exceptions.RequestException as e:
                msg = f"❌ 请求失败: {str(e)}"
                logger.error(msg)
                yield self.create_text_message(msg)
                return

            if response.status_code != 200:
                logger.error(
                    "API status %s: %s", response.status_code, response.text[:300]
                )
                yield self.create_text_message(
                    f"❌ API 响应状态码: {response.status_code}"
                )
                if response.text:
                    yield self.create_text_message(
                        f"🔧 响应内容: {response.text[:500]}"
                    )
                return

            try:
                resp_data = response.json()
            except json.JSONDecodeError as e:
                logger.error(
                    "Failed to parse JSON: %s - %s", str(e), response.text[:300]
                )
                yield self.create_text_message("❌ API 响应解析失败（非JSON）")
                return

            task_id = resp_data.get("id")
            if not task_id:
                yield self.create_text_message("❌ API 响应中未返回任务ID")
                return

            yield self.create_text_message(f"📋 视频生成任务已提交，任务ID: {task_id}")
            yield self.create_text_message("✅ 任务提交成功，可用任务ID查询状态")

            usage = resp_data.get("usage", {})
            if usage:
                if isinstance(usage, dict):
                    yield self.create_text_message("📊 使用统计:")
                    for key, value in usage.items():
                        yield self.create_text_message(f"  - {key}: {value}")
                else:
                    try:
                        usage_text = json.dumps(usage, ensure_ascii=False)
                    except Exception:
                        usage_text = str(usage)
                    yield self.create_text_message(f"📊 使用信息: {usage_text}")

            yield self.create_text_message("🎯 文生视频任务提交完成！")

            result_json = {
                "task_id": task_id,
                "status": "submitted",
                "message": "文生视频任务已提交",
            }
            yield self.create_json_message(result_json)

            logger.info("Text-to-video task submitted")

        except Exception as e:
            error_msg = f"❌ 生成视频时出现未预期错误: {str(e)}"
            logger.exception(error_msg)
            yield self.create_text_message(error_msg)
