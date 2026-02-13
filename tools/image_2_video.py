# author: sawyer-shi

import base64
import json
import logging
from collections.abc import Generator
from io import BytesIO
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage
from PIL import Image

logger = logging.getLogger(__name__)


class Image2VideoTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        Volcengine Ark Contents Generations API image-to-video tool.
        """
        logger.info("Starting image-to-video task (Ark)")

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

            input_image_file = tool_parameters.get("input_image_file")
            if not input_image_file:
                msg = "❌ 请提供输入图像文件"
                logger.warning(msg)
                yield self.create_text_message(msg)
                return

            model = tool_parameters.get("model", "doubao-seedance-1-5-pro-251215")
            resolution = tool_parameters.get("resolution", "720p")
            ratio = tool_parameters.get("ratio", "adaptive")
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

            if duration is not None:
                if duration < 2:
                    duration = 2
                elif duration > 12:
                    duration = 12

            if seed < -1:
                seed = -1
            elif seed > 4294967295:
                seed = 4294967295

            yield self.create_text_message("🚀 图生视频任务启动中...")
            yield self.create_text_message(f"🤖 使用模型: {model}")
            yield self.create_text_message(
                f"📝 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}"
            )
            yield self.create_text_message("⏳ 正在处理输入图像文件...")

            try:
                if hasattr(input_image_file, "blob"):
                    image_bytes = input_image_file.blob
                elif hasattr(input_image_file, "read") and callable(
                    getattr(input_image_file, "read")
                ):
                    image_bytes = input_image_file.read()
                    if isinstance(image_bytes, str):
                        image_bytes = image_bytes.encode("utf-8")
                elif isinstance(input_image_file, bytes):
                    image_bytes = input_image_file
                elif isinstance(input_image_file, str) and input_image_file.startswith("data:"):
                    _, base64_data = input_image_file.split(",", 1)
                    image_bytes = base64.b64decode(base64_data)
                else:
                    raise ValueError(f"不支持的图像数据类型: {type(input_image_file)}")

                if not isinstance(image_bytes, bytes):
                    raise ValueError("图像数据必须是字节格式")

                if len(image_bytes) > 10 * 1024 * 1024:
                    msg = "❌ 输入图片大小超过10MB限制"
                    logger.warning(msg)
                    yield self.create_text_message(msg)
                    return

                image = Image.open(BytesIO(image_bytes))

                if image.mode == "RGBA":
                    background = Image.new("RGB", image.size, (255, 255, 255))
                    background.paste(image, mask=image.split()[3])
                    image = background
                elif image.mode == "P":
                    image = image.convert("RGB")

                img_byte_arr = BytesIO()
                image.save(img_byte_arr, format="PNG")
                png_size = len(img_byte_arr.getvalue())

                if png_size > 10 * 1024 * 1024:
                    img_byte_arr = BytesIO()
                    image.save(img_byte_arr, format="JPEG", quality=95)

                img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")
                data_url = f"data:image/png;base64,{img_base64}"
            except Exception as e:
                yield self.create_text_message(f"❌ 图像处理失败: {str(e)}")
                return

            payload: dict[str, Any] = {
                "model": model,
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
                "resolution": resolution,
                "ratio": ratio,
                "duration": duration,
                "seed": seed,
                "camera_fixed": camera_fixed,
                "watermark": watermark,
                "generate_audio": generate_audio,
                "draft": draft,
                "return_last_frame": return_last_frame,
                "service_tier": service_tier,
            }

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

            yield self.create_text_message("🎯 图生视频任务提交完成！")

            result_json = {
                "task_id": task_id,
                "status": "submitted",
                "message": "图生视频任务已提交",
            }
            yield self.create_json_message(result_json)

            logger.info("Image-to-video task submitted")

        except Exception as e:
            error_msg = f"❌ 生成视频时出现未预期错误: {str(e)}"
            logger.exception(error_msg)
            yield self.create_text_message(error_msg)
