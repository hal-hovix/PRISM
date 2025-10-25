
from typing import Dict, List


class MockNotion:
    def fetch_pages(self) -> List[Dict]:
        return []

    def fetch_page(self, id: str) -> Dict:
        return {"id": id, "title": "Sample", "body": ""}

    def update_tags(self, id: str, tags: List[str]) -> Dict:
        return {"id": id, "tags": tags}


