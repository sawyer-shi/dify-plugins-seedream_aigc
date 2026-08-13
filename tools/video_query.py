# author: sawyer-shi

import json
import logging
from collections.abc import Generator
from typing import Any

import requests
from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

logger = logging.getLogger(__name__)


class VideoQueryTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        """
        Volcengine Ark Contents Generations API video query tool.
        """
        logger.info("Starting video query task (Ark)")

        try:
            credential = self.runtime.credentials.get("api_key")
            if not credential:
                msg = "❌ API密钥未配置"
                logger.error(msg)
                yield self.create_text_message(msg)
                return

            task_id = tool_parameters.get("task_id", "").strip()
            if not task_id:
                msg = "❌ 请输入任务ID"
                logger.warning(msg)
                yield self.create_text_message(msg)
                return

            download_video = tool_parameters.get("download_video", "true") == "true"

            api_url = (
                "https://ark.cn-beijing.volces.com/api/v3/contents/generations/tasks/"
                f"{task_id}"
            )
            headers = {
                "Authorization": f"Bearer {credential}",
                "Content-Type": "application/json",
            }

            yield self.create_text_message("🔍 正在查询视频生成结果...")
            yield self.create_text_message(f"📋 任务ID: {task_id}")
            yield self.create_text_message("⏳ 正在连接火山方舟 API...")

            try:
                response = requests.get(api_url, headers=headers, timeout=60)
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

            task_id_result = resp_data.get("id")
            status = resp_data.get("status")
            content = resp_data.get("content", {})
            video_url = content.get("video_url")
            last_frame_url = content.get("last_frame_url")

            yield self.create_text_message("✅ 查询成功")
            yield self.create_text_message(f"📋 任务ID: {task_id_result}")
            yield self.create_text_message(f"📊 状态: {status}")
            if video_url:
                yield self.create_text_message(f"🎬 视频链接: {video_url}")
                if download_video:
                    yield self.create_text_message("⬇️ 正在下载视频文件...")
                    try:
                        video_response = requests.get(video_url, timeout=120)
                        if video_response.status_code == 200:
                            yield self.create_blob_message(
                                blob=video_response.content,
                                meta={"mime_type": "video/mp4", "filename": f"{task_id_result}.mp4"},
                            )
                            yield self.create_text_message("✅ 视频下载完成")
                        else:
                            yield self.create_text_message(
                                f"❌ 视频下载失败，状态码: {video_response.status_code}"
                            )
                    except requests.exceptions.RequestException as e:
                        yield self.create_text_message(f"❌ 视频下载失败: {str(e)}")
            if last_frame_url:
                yield self.create_text_message(f"🖼️ 尾帧链接: {last_frame_url}")

            result_json = {
                "task_id": task_id_result,
                "status": status,
                "video_url": video_url,
                "last_frame_url": last_frame_url,
                "model": resp_data.get("model"),
                "error": resp_data.get("error"),
                "seed": resp_data.get("seed"),
                "resolution": resp_data.get("resolution"),
                "ratio": resp_data.get("ratio"),
                "duration": resp_data.get("duration"),
                "frames": resp_data.get("frames"),
                "frames_per_second": resp_data.get("framespersecond"),
                "usage": resp_data.get("usage"),
                "created_at": resp_data.get("created_at"),
                "updated_at": resp_data.get("updated_at"),
            }
            yield self.create_json_message(result_json)

            logger.info("Video query completed")

        except Exception as e:
            error_msg = f"❌ 查询视频结果时出现未预期错误: {str(e)}"
            logger.exception(error_msg)
            yield self.create_text_message(error_msg)
