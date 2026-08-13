# author: sawyer-shi

from typing import Any

import requests
from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError


class SeedreamAigcProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            credential = credentials.get("api_key")
            if not credential:
                raise ToolProviderCredentialValidationError("Volcengine API key is required")
            if len(credential) < 36:
                raise ToolProviderCredentialValidationError("Volcengine API key length is invalid")
            self._test_volcengine_connection(credential)
        except Exception as e:
            raise ToolProviderCredentialValidationError(
                f"Volcengine API credential validation failed: {str(e)}"
            )

    def _test_volcengine_connection(self, credential: str) -> None:
        url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {credential}",
        }
        payload = {
            "model": "glm-5-2-260617",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello!"},
            ],
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=10)
        except requests.RequestException as req_err:
            raise ToolProviderCredentialValidationError(
                f"Unable to reach Volcengine service: {req_err}"
            )

        if response.status_code != 200:
            try:
                data = response.json()
                error_message = (
                    data.get("error", {}).get("message")
                    or data.get("message")
                    or response.text
                )
            except Exception:
                error_message = response.text
            raise ToolProviderCredentialValidationError(
                f"Volcengine API error {response.status_code}: {error_message}"
            )

        try:
            data = response.json()
        except ValueError:
            raise ToolProviderCredentialValidationError(
                "Volcengine API returned non-JSON response"
            )

        choices = data.get("choices")
        if not isinstance(choices, list) or len(choices) == 0:
            raise ToolProviderCredentialValidationError(
                "Volcengine API response missing valid choices"
            )
