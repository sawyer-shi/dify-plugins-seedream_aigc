# author: sawyer-shi

import json
import logging
from collections.abc import Generator
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools._video_models import (
    DEFAULT_VIDEO_MODEL,
    extra_payload,
    normalize_core_params,
    resolve_model,
    tier_payload,
)

logger = logging.getLogger(__name__)


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

            model = resolve_model(tool_parameters.get("model", DEFAULT_VIDEO_MODEL))
            ratio = tool_parameters.get("ratio", "16:9")
            camera_fixed = tool_parameters.get("camera_fixed", "false") == "true"
            watermark = tool_parameters.get("watermark", "false") == "true"
            generate_audio = tool_parameters.get("generate_audio", "true") == "true"
            service_tier = tool_parameters.get("service_tier", "default")
            bitrate_mode = tool_parameters.get("bitrate_mode", "standard")
            output_format = tool_parameters.get("output_format", "mp4")
            priority = max(0, min(9, int(tool_parameters.get("priority", 0) or 0)))
            web_search = tool_parameters.get("web_search", "false") == "true"

            if len(prompt) > 500:
                prompt = prompt[:500]

            core = normalize_core_params(
                model,
                duration=tool_parameters.get("duration", 5),
                resolution=tool_parameters.get("resolution", "720p"),
                seed=tool_parameters.get("seed", -1),
                draft=tool_parameters.get("draft", "false") == "true",
                return_last_frame=tool_parameters.get(
                    "return_last_frame", "false"
                ) == "true",
            )
            resolution = core["resolution"]
            duration = core["duration"]
            seed = core["seed"]
            draft = core["draft"]
            return_last_frame = core["return_last_frame"]

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
            payload.update(
                tier_payload(
                    model,
                    camera_fixed=camera_fixed,
                    service_tier=service_tier,
                    bitrate_mode=bitrate_mode,
                )
            )
            payload.update(
                extra_payload(
                    model,
                    output_format=output_format,
                    priority=priority,
                    web_search=web_search,
                )
            )

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
