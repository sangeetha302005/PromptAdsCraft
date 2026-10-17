"""
storage.py
----------
Local JSON-based campaign history storage.
Stores campaigns in a single JSON file (campaigns.json by default).

Features:
- Campaign persistence (save, list, load, update, delete)
- Search and filtering by platform, status, and keywords
- Metric calculation (total, completed, drafts, real average quality score)
- Graceful corruption recovery

Limitations (documented):
- Single-file storage is suitable for personal/local/demo use only.
- Not thread-safe for concurrent writes across distributed instances.
- Not a multi-user enterprise database.
- Data is stored in plain JSON locally on disk.
- Corrupt JSON is handled gracefully by resetting to a valid empty store.
"""

from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


class CampaignStorage:
    """Manages local JSON campaign history."""

    def __init__(self, storage_path: str = "campaigns.json"):
        self.path = Path(storage_path)
        self._ensure_file()

    def _ensure_file(self) -> None:
        """Create the storage file with an empty campaigns list if it doesn't exist."""
        if not self.path.exists():
            self._write_data({"campaigns": []})

    def _read_data(self) -> dict:
        """Read and parse JSON storage. Returns empty structure on any error."""
        try:
            content = self.path.read_text(encoding="utf-8")
            data = json.loads(content)
            if "campaigns" not in data or not isinstance(data["campaigns"], list):
                return {"campaigns": []}
            return data
        except (json.JSONDecodeError, OSError, ValueError):
            return {"campaigns": []}

    def _write_data(self, data: dict) -> None:
        """Write data to JSON file safely."""
        self.path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def save_campaign(
        self,
        campaign_data: dict,
        campaign_name: str = "",
        status: str = "Completed",
    ) -> str:
        """
        Save a campaign to history.
        Returns the unique 8-character campaign ID.
        """
        data = self._read_data()
        campaign_id = str(uuid.uuid4())[:8].upper()
        timestamp = datetime.now(timezone.utc).isoformat()

        # Extract quality score if available
        quality_score = None
        qr = campaign_data.get("quality_review")
        if isinstance(qr, dict) and "overall_score" in qr:
            quality_score = qr["overall_score"]

        entry = {
            "id": campaign_id,
            "name": campaign_name or f"Campaign {campaign_id}",
            "created_at": timestamp,
            "updated_at": timestamp,
            "status": status,
            "brand_name": campaign_data.get("inputs", {}).get("brand_name", "Unknown"),
            "product_name": campaign_data.get("inputs", {}).get("product_name", "Unknown"),
            "platform": campaign_data.get("inputs", {}).get("platform", "Unknown"),
            "quality_score": quality_score,
            "data": campaign_data,
        }
        data["campaigns"].insert(0, entry)
        # Keep only the last 50 campaigns
        data["campaigns"] = data["campaigns"][:50]
        self._write_data(data)
        return campaign_id

    def update_campaign(
        self,
        campaign_id: str,
        campaign_data: dict,
        campaign_name: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bool:
        """
        Update an existing campaign by ID.
        Returns True if updated, False if campaign was not found.
        """
        data = self._read_data()
        updated = False
        timestamp = datetime.now(timezone.utc).isoformat()

        for c in data["campaigns"]:
            if c["id"] == campaign_id:
                c["data"] = campaign_data
                c["updated_at"] = timestamp
                if campaign_name:
                    c["name"] = campaign_name
                if status:
                    c["status"] = status
                c["brand_name"] = campaign_data.get("inputs", {}).get("brand_name", c.get("brand_name", "Unknown"))
                c["product_name"] = campaign_data.get("inputs", {}).get("product_name", c.get("product_name", "Unknown"))
                c["platform"] = campaign_data.get("inputs", {}).get("platform", c.get("platform", "Unknown"))

                qr = campaign_data.get("quality_review")
                if isinstance(qr, dict) and "overall_score" in qr:
                    c["quality_score"] = qr["overall_score"]
                updated = True
                break

        if updated:
            self._write_data(data)
        return updated

    def list_campaigns(
        self,
        query: Optional[str] = None,
        platform_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
    ) -> list[dict]:
        """
        Return a list of campaign summaries (without full data payload),
        optionally filtered by search query, platform, and status.
        """
        data = self._read_data()
        results = []

        q = (query or "").strip().lower()
        p_filter = (platform_filter or "").strip()
        s_filter = (status_filter or "").strip()

        for c in data["campaigns"]:
            # Status check
            status = c.get("status", "Completed")
            if s_filter and s_filter != "All" and status.lower() != s_filter.lower():
                continue

            # Platform check
            platform = c.get("platform", "")
            if p_filter and p_filter != "All" and platform.lower() != p_filter.lower():
                continue

            # Query check
            if q:
                name = c.get("name", "").lower()
                brand = c.get("brand_name", "").lower()
                product = c.get("product_name", "").lower()
                if q not in name and q not in brand and q not in product:
                    continue

            results.append({
                "id": c["id"],
                "name": c["name"],
                "created_at": c["created_at"],
                "updated_at": c.get("updated_at", c["created_at"]),
                "status": status,
                "brand_name": c.get("brand_name", ""),
                "product_name": c.get("product_name", ""),
                "platform": c.get("platform", ""),
                "quality_score": c.get("quality_score"),
            })

        return results

    def load_campaign(self, campaign_id: str) -> Optional[dict]:
        """Load full campaign data by ID. Returns None if not found."""
        data = self._read_data()
        for c in data["campaigns"]:
            if c["id"] == campaign_id:
                return c["data"]
        return None

    def delete_campaign(self, campaign_id: str) -> bool:
        """Delete a campaign by ID. Returns True if deleted, False if not found."""
        data = self._read_data()
        original_count = len(data["campaigns"])
        data["campaigns"] = [c for c in data["campaigns"] if c["id"] != campaign_id]
        if len(data["campaigns"]) < original_count:
            self._write_data(data)
            return True
        return False

    def clear_all(self) -> None:
        """Delete all campaigns. Irreversible."""
        self._write_data({"campaigns": []})

    def campaign_count(self) -> int:
        """Return total number of saved campaigns."""
        return len(self._read_data()["campaigns"])

    def get_metrics(self) -> dict:
        """
        Calculate metrics grounded strictly in actual saved application data.
        Never fabricates or hardcodes placeholder metrics.
        """
        campaigns = self._read_data()["campaigns"]
        total = len(campaigns)
        completed = sum(1 for c in campaigns if c.get("status", "Completed") == "Completed")
        drafts = sum(1 for c in campaigns if c.get("status") == "Draft")

        scores = [
            c["quality_score"]
            for c in campaigns
            if c.get("quality_score") is not None and isinstance(c["quality_score"], (int, float))
        ]

        avg_score = round(sum(scores) / len(scores), 1) if scores else None

        return {
            "total_campaigns": total,
            "completed_campaigns": completed,
            "draft_campaigns": drafts,
            "avg_quality_score": avg_score,
            "total_scored_campaigns": len(scores),
        }
