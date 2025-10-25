import os
import time
from typing import List

from src.api.core.logging import configure_logging
from src.api.core.mcp_client import MockMCP
from src.api.core.notion_client import MockNotion


def run_once():
    mcp = MockMCP()
    notion = MockNotion()
    pages: List[dict] = mcp.fetch_pages() or notion.fetch_pages()
    # No store yet; just log size
    print(f"Synced pages: {len(pages)}")


def main():
    configure_logging()
    interval = int(os.getenv("WORKER_INTERVAL", "60"))
    while True:
        run_once()
        time.sleep(interval)


if __name__ == "__main__":
    main()

