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

SEEDANCE_2_MODELS = {
    "doubao-seedance-2-0-260128",
    "doubao-seedance-2-0-fast-260128",
}

MODEL_ALIASES = {
    "doubao-seedance-2-0-fast-250428": "doubao-seedance-2-0-fast-260128",
}

MODE_RULES: dict[str, dict[str, Any]] = {
    "text_video": {
        "label": "文本（可选）+ 视频",
        "need_image": False,
        "need_video": True,
        "need_audio": False,
    },
    "text_image_audio": {
        "label": "文本（可选）+ 图片 + 音频",
        "need_image": True,
        "need_video": False,
        "need_audio": True,
    },
    "text_image_video": {
        "label": "文本（可选）+ 图片 + 视频",
        "need_image": True,
        "need_video": True,
        "need_audio": False,
    },
    "text_video_audio": {
        "label": "文本（可选）+ 视频 + 音频",
        "need_image": False,
        "need_video": True,
        "need_audio": True,
    },
    "text_image_video_audio": {
        "label": "文本（可选）+ 图片 + 视频 + 音频",
        "need_image": True,
        "need_video": True,
        "need_audio": True,
    },
}


def _is_seedance_2_series(model: str) -> bool:
    normalized = model.lower()
    return normalized in SEEDANCE_2_MODELS or "seedance-2-0" in normalized


class MultimodalReference2VideoTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        Volcengine Ark Contents Generations API multimodal reference video tool
        (Seedance 2.0 series only).
        """
        logger.info("Starting multimodal reference video task (Ark)")

        try:
            api_key = self.runtime.credentials.get("api_key")
            if not api_key:
                msg = "❌ API密钥未配置"
                logger.error(msg)
                yield self.create_text_message(msg)
                return

            mode = tool_parameters.get("input_mode", "text_image_video")
            mode_rule = MODE_RULES.get(mode)
            if not mode_rule:
                msg = "❌ 输入组合无效，请重新选择"
                logger.warning(msg)
                yield self.create_text_message(msg)
                return

            model = tool_parameters.get("model", "doubao-seedance-2-0-260128")
            model = MODEL_ALIASES.get(model, model)
            if not _is_seedance_2_series(model):
                msg = "❌ 多模态参考生视频仅支持 Seedance 2.0 / 2.0 Fast 模型"
                logger.warning(msg)
                yield self.create_text_message(msg)
                return

            prompt = tool_parameters.get("prompt", "").strip()
            if len(prompt) > 500:
                prompt = prompt[:500]

            image_files = self._to_list(tool_parameters.get("reference_image_files"))
            video_urls = self._parse_url_list(tool_parameters.get("reference_video_urls", ""))
            audio_files = self._to_list(tool_parameters.get("reference_audio_files"))

            if mode_rule["need_image"] and not image_files:
                msg = f"❌ 当前组合为 {mode_rule['label']}，请至少上传 1 张参考图片"
                logger.warning(msg)
                yield self.create_text_message(msg)
                return

            if mode_rule["need_video"] and not video_urls:
                msg = f"❌ 当前组合为 {mode_rule['label']}，请至少提供 1 个参考视频 URL"
                logger.warning(msg)
                yield self.create_text_message(msg)
                return

            if mode_rule["need_audio"] and not audio_files:
                msg = f"❌ 当前组合为 {mode_rule['label']}，请至少上传 1 段参考音频"
                logger.warning(msg)
                yield self.create_text_message(msg)
                return

            if len(image_files) > 9:
                yield self.create_text_message("❌ 参考图片最多支持 9 张")
                return

            if len(video_urls) > 3:
                yield self.create_text_message("❌ 参考视频 URL 最多支持 3 个")
                return

            if len(audio_files) > 3:
                yield self.create_text_message("❌ 参考音频最多支持 3 段")
                return

            if mode_rule["need_audio"] and not (image_files or video_urls):
                yield self.create_text_message("❌ 不可单独输入音频，至少需要图片或视频")
                return

            resolution = tool_parameters.get("resolution", "720p")
            ratio = tool_parameters.get("ratio", "adaptive")
            duration = tool_parameters.get("duration", 5)
            seed = tool_parameters.get("seed", -1)
            watermark = tool_parameters.get("watermark", "true") == "true"
            generate_audio = tool_parameters.get("generate_audio", "true") == "true"
            return_last_frame = (
                tool_parameters.get("return_last_frame", "false") == "true"
            )

            if resolution == "1080p":
                resolution = "720p"

            if duration == -1:
                pass
            elif duration is not None:
                if duration < 4:
                    duration = 4
                elif duration > 15:
                    duration = 15

            if seed < -1:
                seed = -1
            elif seed > 4294967295:
                seed = 4294967295

            yield self.create_text_message("🚀 多模态参考生视频任务启动中...")
            yield self.create_text_message(f"🤖 使用模型: {model}")
            yield self.create_text_message(f"🧩 输入组合: {mode_rule['label']}")
            if prompt:
                yield self.create_text_message(
                    f"📝 提示词: {prompt[:100]}{'...' if len(prompt) > 100 else ''}"
                )
            else:
                yield self.create_text_message("📝 提示词: 未填写（可选）")

            content: list[dict[str, Any]] = []
            if prompt:
                content.append({"type": "text", "text": prompt})

            if image_files:
                yield self.create_text_message("⏳ 正在处理参考图片...")
                for i, image_file in enumerate(image_files):
                    try:
                        image_data_url = self._encode_image(image_file)
                    except Exception as e:
                        yield self.create_text_message(
                            f"❌ 第 {i + 1} 张图片处理失败: {str(e)}"
                        )
                        return

                    content.append(
                        {
                            "type": "image_url",
                            "image_url": {"url": image_data_url},
                            "role": "reference_image",
                        }
                    )

            if video_urls:
                for video_url in video_urls:
                    content.append(
                        {
                            "type": "video_url",
                            "video_url": {"url": video_url},
                            "role": "reference_video",
                        }
                    )

            if audio_files:
                yield self.create_text_message("⏳ 正在处理参考音频...")
                for i, audio_file in enumerate(audio_files):
                    try:
                        audio_data_url = self._encode_audio(audio_file)
                    except Exception as e:
                        yield self.create_text_message(
                            f"❌ 第 {i + 1} 段音频处理失败: {str(e)}"
                        )
                        return

                    content.append(
                        {
                            "type": "audio_url",
                            "audio_url": {"url": audio_data_url},
                            "role": "reference_audio",
                        }
                    )

            payload: dict[str, Any] = {
                "model": model,
                "content": content,
                "resolution": resolution,
                "ratio": ratio,
                "duration": duration,
                "seed": seed,
                "watermark": watermark,
                "generate_audio": generate_audio,
                "return_last_frame": return_last_frame,
            }

            api_url = "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
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
                logger.error("API status %s: %s", response.status_code, response.text[:300])
                yield self.create_text_message(
                    f"❌ API 响应状态码: {response.status_code}"
                )
                if response.text:
                    yield self.create_text_message(f"🔧 响应内容: {response.text[:500]}")
                return

            try:
                resp_data = response.json()
            except json.JSONDecodeError as e:
                logger.error("Failed to parse JSON: %s - %s", str(e), response.text[:300])
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

            yield self.create_text_message("🎯 多模态参考生视频任务提交完成！")

            result_json = {
                "task_id": task_id,
                "status": "submitted",
                "message": "多模态参考生视频任务已提交",
                "input_mode": mode,
            }
            yield self.create_json_message(result_json)

            logger.info("Multimodal reference video task submitted")

        except Exception as e:
            error_msg = f"❌ 提交多模态参考生视频任务时出现未预期错误: {str(e)}"
            logger.exception(error_msg)
            yield self.create_text_message(error_msg)

    @staticmethod
    def _to_list(value: Any) -> list[Any]:
        if value is None:
            return []
        if isinstance(value, list):
            return [item for item in value if item is not None]
        return [value]

    @staticmethod
    def _parse_url_list(raw_value: Any) -> list[str]:
        if not raw_value:
            return []

        if isinstance(raw_value, list):
            items = [str(item).strip() for item in raw_value]
        else:
            text = str(raw_value)
            normalized = text.replace("\n", ",").replace("，", ",").replace(";", ",")
            items = [chunk.strip() for chunk in normalized.split(",")]

        urls = [item for item in items if item]
        valid_urls: list[str] = []
        for url in urls:
            if (
                url.startswith("http://")
                or url.startswith("https://")
                or url.startswith("asset://")
            ):
                valid_urls.append(url)

        return valid_urls

    @staticmethod
    def _encode_image(input_image_file: Any) -> str:
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
        elif isinstance(input_image_file, str):
            if input_image_file.startswith("data:image/"):
                return input_image_file
            if input_image_file.startswith("http://") or input_image_file.startswith(
                "https://"
            ):
                return input_image_file
            if input_image_file.startswith("asset://"):
                return input_image_file
            raise ValueError("不支持的图片字符串格式")
        else:
            raise ValueError(f"不支持的图像数据类型: {type(input_image_file)}")

        if not isinstance(image_bytes, bytes):
            raise ValueError("图像数据必须是字节格式")

        if len(image_bytes) > 30 * 1024 * 1024:
            raise ValueError("输入图片大小超过30MB限制")

        image = Image.open(BytesIO(image_bytes))
        if image.mode == "RGBA":
            background = Image.new("RGB", image.size, (255, 255, 255))
            background.paste(image, mask=image.split()[3])
            image = background
        elif image.mode == "P":
            image = image.convert("RGB")

        img_byte_arr = BytesIO()
        image.save(img_byte_arr, format="PNG")
        img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")
        return f"data:image/png;base64,{img_base64}"

    @staticmethod
    def _encode_audio(input_audio_file: Any) -> str:
        if isinstance(input_audio_file, str):
            if input_audio_file.startswith("data:audio/"):
                return input_audio_file
            if input_audio_file.startswith("http://") or input_audio_file.startswith(
                "https://"
            ):
                return input_audio_file
            if input_audio_file.startswith("asset://"):
                return input_audio_file
            raise ValueError("不支持的音频字符串格式")

        if hasattr(input_audio_file, "blob"):
            audio_bytes = input_audio_file.blob
        elif hasattr(input_audio_file, "read") and callable(
            getattr(input_audio_file, "read")
        ):
            audio_bytes = input_audio_file.read()
            if isinstance(audio_bytes, str):
                audio_bytes = audio_bytes.encode("utf-8")
        elif isinstance(input_audio_file, bytes):
            audio_bytes = input_audio_file
        else:
            raise ValueError(f"不支持的音频数据类型: {type(input_audio_file)}")

        if not isinstance(audio_bytes, bytes):
            raise ValueError("音频数据必须是字节格式")

        if len(audio_bytes) > 15 * 1024 * 1024:
            raise ValueError("输入音频大小超过15MB限制")

        audio_ext = MultimodalReference2VideoTool._guess_audio_ext(input_audio_file)
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        return f"data:audio/{audio_ext};base64,{audio_base64}"

    @staticmethod
    def _guess_audio_ext(input_audio_file: Any) -> str:
        mime_type = str(getattr(input_audio_file, "mime_type", "") or "").lower()
        filename = str(getattr(input_audio_file, "filename", "") or "").lower()

        if "wav" in mime_type or filename.endswith(".wav"):
            return "wav"

        return "mp3"
