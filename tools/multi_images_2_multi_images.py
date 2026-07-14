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

from tools._capabilities import (
    DEFAULT_MODEL,
    MAX_INPUT_IMAGE_BYTES,
    assert_input_images_count,
    assert_size_for_model,
    get_caps,
)

logger = logging.getLogger(__name__)


class MultiImageFiles2MultiImagesTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        Volcengine Ark Images Generations API multi-reference group image tool.
        """
        logger.info("Starting multi-reference group image task (Ark)")

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

            input_image_files = tool_parameters.get("input_image_files", [])
            if not input_image_files or not isinstance(input_image_files, list):
                msg = "❌ 请提供输入图像文件数组"
                logger.warning(msg)
                yield self.create_text_message(msg)
                return

            model = tool_parameters.get("model", DEFAULT_MODEL)
            size = tool_parameters.get("size", "2048x2048")
            output_format = tool_parameters.get("output_format", "jpeg")
            max_images = int(tool_parameters.get("max_images", 4))
            watermark = tool_parameters.get("watermark", "true") == "true"

            try:
                assert_size_for_model(size, model)
                assert_input_images_count(len(input_image_files), model)
            except ValueError as e:
                yield self.create_text_message(f"❌ {str(e)}")
                return

            caps = get_caps(model)

            yield self.create_text_message("🚀 多参考图生组图任务启动中...")
            yield self.create_text_message(f"🤖 使用模型: {caps['label']}")
            yield self.create_text_message(
                f"📝 提示词: {prompt[:50]}{'...' if len(prompt) > 50 else ''}"
            )
            yield self.create_text_message(f"📷 参考图片数量: {len(input_image_files)}")
            yield self.create_text_message("⏳ 正在处理输入图像文件...")

            valid_image_data_urls = []
            for i, input_image_file in enumerate(input_image_files):
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
                    elif isinstance(input_image_file, str) and input_image_file.startswith(
                        "data:"
                    ):
                        _, base64_data = input_image_file.split(",", 1)
                        image_bytes = base64.b64decode(base64_data)
                    else:
                        raise ValueError(
                            f"不支持的图像数据类型: {type(input_image_file)}"
                        )

                    if not isinstance(image_bytes, bytes):
                        raise ValueError("图像数据必须是字节格式")

                    if len(image_bytes) > MAX_INPUT_IMAGE_BYTES:
                        msg = f"❌ 第 {i + 1} 张输入图片大小超过{MAX_INPUT_IMAGE_BYTES // 1024 // 1024}MB限制"
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

                    if png_size > MAX_INPUT_IMAGE_BYTES:
                        img_byte_arr = BytesIO()
                        image.save(img_byte_arr, format="JPEG", quality=95)

                    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")
                    data_url = f"data:image/png;base64,{img_base64}"
                    valid_image_data_urls.append(data_url)
                except Exception as e:
                    yield self.create_text_message(
                        f"❌ 第 {i + 1} 张图像处理失败: {str(e)}"
                    )
                    return

            yield self.create_text_message(f"📐 图像尺寸: {size}")
            yield self.create_text_message("⏳ 正在连接火山方舟 API...")

            payload = {
                "model": model,
                "prompt": prompt,
                "image": valid_image_data_urls,
                "size": size,
                "watermark": watermark,
                "response_format": "b64_json",
            }
            if caps["supports_stream"]:
                payload["stream"] = False
            if caps["supports_output_format"]:
                payload["output_format"] = output_format
            if caps["supports_sequential"]:
                payload["sequential_image_generation"] = "auto"
                payload["sequential_image_generation_options"] = {"max_images": max_images}

            logger.info("Submitting request: %s", json.dumps(payload, ensure_ascii=False))
            yield self.create_text_message("🎨 正在生成组图，请稍候...")

            try:
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=360,
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

            yield self.create_text_message("🎉 组图生成成功！")

            actual_format = output_format if caps["supports_output_format"] else "jpeg"
            mime_type = f"image/{actual_format}"

            for i, data in enumerate(data_list):
                b64_json = data.get("b64_json", "")
                image_size_text = data.get("size", "")
                if not b64_json:
                    yield self.create_text_message(
                        f"❌ 未获取到第 {i + 1} 张图片的Base64数据"
                    )
                    return

                try:
                    image_bytes = base64.b64decode(b64_json)
                    yield self.create_blob_message(
                        blob=image_bytes,
                        meta={"mime_type": mime_type},
                    )
                except Exception as e:
                    logger.error("Failed to decode image: %s", str(e))
                    yield self.create_text_message(f"❌ 处理图像失败: {str(e)}")
                    return

                info_text = f"✅ 第 {i + 1} 张图片生成完成！\n"
                if image_size_text:
                    info_text += f"📐 尺寸: {image_size_text}\n"
                info_text += f"💾 大小: {len(image_bytes) / 1024 / 1024:.2f} MB"
                yield self.create_text_message(info_text)

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

            yield self.create_text_message("🎯 多参考图生组图任务完成！")
            logger.info("Multi-reference group image task completed")

        except Exception as e:
            error_msg = f"❌ 生成图像时出现未预期错误: {str(e)}"
            logger.exception(error_msg)
            yield self.create_text_message(error_msg)
