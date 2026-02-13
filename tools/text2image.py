# author: sawyer-shi

import json
import logging
from collections.abc import Generator
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

logger = logging.getLogger(__name__)


class Text2ImageTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        Volcengine Ark Images Generations API text-to-image tool.
        """
        logger.info("Starting text-to-image task (Ark)")

        try:
            api_key = self.runtime.credentials.get("api_key")
            if not api_key:
                msg = "❌ API密钥未配置"
                logger.error(msg)
                yield self.create_text_message(msg)
                return

            api_url = "https://ark.cn-beijing.volces.com/api/v3/images/generations"
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

            size = tool_parameters.get("size", "2048x2048")
            sequential_image_generation = tool_parameters.get(
                "sequential_image_generation", "disabled"
            )
            watermark = tool_parameters.get("watermark", "true") == "true"
            model = tool_parameters.get("model", "doubao-seedream-4-5-251128")

            yield self.create_text_message("🚀 文生图任务启动中...")
            yield self.create_text_message(f"🤖 使用模型: {model}")
            yield self.create_text_message(
                f"📝 提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"
            )
            yield self.create_text_message(f"📐 图像尺寸: {size}")
            yield self.create_text_message("⏳ 正在连接火山方舟 API...")

            payload = {
                "model": model,
                "prompt": prompt,
                "size": size,
                "sequential_image_generation": sequential_image_generation,
                "stream": False,
                "response_format": "url",
                "watermark": watermark,
            }

            logger.info("Submitting request: %s", json.dumps(payload, ensure_ascii=False))
            yield self.create_text_message("🎨 正在生成图像，请稍候...")

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

            data_list = resp_data.get("data", [])
            if not data_list:
                yield self.create_text_message("❌ API 响应中未返回图像数据")
                return

            yield self.create_text_message("🎉 图像生成成功！")

            for i, data in enumerate(data_list):
                image_url = data.get("url", "")
                image_size_text = data.get("size", "")
                if not image_url:
                    yield self.create_text_message(
                        f"❌ 未获取到第 {i + 1} 张图片的URL"
                    )
                    return

                yield self.create_image_message(image_url)

                info_text = f"✅ 第 {i + 1} 张图片生成完成！\n"
                if image_size_text:
                    info_text += f"📐 尺寸: {image_size_text}\n"
                yield self.create_text_message(info_text.rstrip())

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

            yield self.create_text_message("🎯 文生图任务完成！")
            logger.info("Text-to-image task completed")

        except Exception as e:
            error_msg = f"❌ 生成图像时出现未预期错误: {str(e)}"
            logger.exception(error_msg)
            yield self.create_text_message(error_msg)
