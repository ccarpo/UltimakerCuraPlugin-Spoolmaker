import json
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class SpoolmanError(Exception):
    pass


class SpoolmanClient:
    def __init__(self, base_url: str = "http://192.168.1.60:5021", timeout_seconds: int = 15) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout_seconds = timeout_seconds

    @property
    def base_url(self) -> str:
        return self._base_url

    def fetch_spools(self, allow_archived: bool = False) -> List[Dict[str, Any]]:
        query_string = urlencode({"allow_archived": str(allow_archived).lower()})
        request_url = f"{self._base_url}/api/v1/spool?{query_string}"
        request = Request(
            request_url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Cura-Spoolman-Materials/0.1.0"
            }
        )

        try:
            with urlopen(request, timeout=self._timeout_seconds) as response:
                status_code = getattr(response, "status", response.getcode())
                if status_code < 200 or status_code >= 300:
                    raise SpoolmanError(f"Spoolman returned HTTP {status_code}.")

                charset = response.headers.get_content_charset("utf-8")
                payload = json.loads(response.read().decode(charset))
        except HTTPError as error:
            raise SpoolmanError(f"Spoolman returned HTTP {error.code}.") from error
        except URLError as error:
            raise SpoolmanError(f"Unable to reach Spoolman at {self._base_url}: {error.reason}") from error
        except TimeoutError as error:
            raise SpoolmanError(f"Timed out while connecting to Spoolman at {self._base_url}.") from error
        except json.JSONDecodeError as error:
            raise SpoolmanError("Spoolman returned invalid JSON.") from error

        if not isinstance(payload, list):
            raise SpoolmanError("Unexpected response from Spoolman: expected a list of spools.")

        return payload
