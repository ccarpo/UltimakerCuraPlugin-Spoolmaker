import json
from typing import Any, Dict, List
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


class SpoolmanError(Exception):
    pass


class SpoolmanClient:
    DEFAULT_BASE_URL = "http://192.168.1.60:5021"

    def __init__(self, base_url: str = DEFAULT_BASE_URL, timeout_seconds: int = 15) -> None:
        self._base_url = self.normalize_base_url(base_url)
        self._timeout_seconds = timeout_seconds

    @property
    def base_url(self) -> str:
        return self._base_url

    def set_base_url(self, base_url: str) -> None:
        self._base_url = self.normalize_base_url(base_url)

    def fetch_spools(self, allow_archived: bool = False) -> List[Dict[str, Any]]:
        query_string = urlencode({"allow_archived": str(allow_archived).lower()})
        payload = self._request_json(f"/api/v1/spool?{query_string}")

        if not isinstance(payload, list):
            raise SpoolmanError("Unexpected response from Spoolman: expected a list of spools.")

        return payload

    def test_connection(self) -> Dict[str, Any]:
        spools = self.fetch_spools(allow_archived=False)
        return {
            "base_url": self._base_url,
            "spool_count": len(spools),
        }

    @classmethod
    def normalize_base_url(cls, base_url: str) -> str:
        if not isinstance(base_url, str):
            raise SpoolmanError("The Spoolman URL must be a string.")

        candidate = base_url.strip()
        if not candidate:
            raise SpoolmanError("The Spoolman URL cannot be empty.")

        parsed = urlparse(candidate)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise SpoolmanError("Enter a full Spoolman URL, for example http://localhost:7912")

        path = parsed.path.rstrip("/")
        if path.endswith("/api/v1"):
            path = path[:-7]

        normalized_url = f"{parsed.scheme}://{parsed.netloc}{path}"
        return normalized_url.rstrip("/")

    def _request_json(self, path: str) -> Any:
        request_url = f"{self._base_url}{path}"
        request = Request(
            request_url,
            headers={
                "Accept": "application/json",
                "User-Agent": "Cura-Spoolman-Materials/0.2.0"
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

        return payload
