from __future__ import annotations

from .client import FireflyClient
from .config import Settings, read_token_file
from .server import create_mcp
from .service import FireflyService


def main() -> None:
    settings = Settings.from_environment()
    token = read_token_file(settings.token_file)
    client = FireflyClient(base_url=settings.base_url, token=token, timeout_seconds=settings.timeout_seconds)
    mcp = create_mcp(FireflyService(client))
    mcp.run(transport="stdio", show_banner=False)


if __name__ == "__main__":
    main()
