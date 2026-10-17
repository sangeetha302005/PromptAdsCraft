"""
test_storage.py
Tests for campaign history storage.
"""
import json
import os
import pytest
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.storage import CampaignStorage


SAMPLE_CAMPAIGN = {
    "inputs": {
        "brand_name": "StoreBrand",
        "product_name": "StoreProduct",
        "platform": "Instagram Reels",
    },
    "brief": {"summary": "Test campaign."},
}


@pytest.fixture
def storage(tmp_path):
    """Provide a fresh CampaignStorage backed by a temp file."""
    store_path = str(tmp_path / "test_campaigns.json")
    return CampaignStorage(storage_path=store_path)


def test_storage_creates_file(tmp_path):
    path = str(tmp_path / "new_campaigns.json")
    CampaignStorage(storage_path=path)
    assert Path(path).exists()


def test_save_campaign_returns_id(storage):
    campaign_id = storage.save_campaign(SAMPLE_CAMPAIGN, "Test Campaign")
    assert isinstance(campaign_id, str)
    assert len(campaign_id) > 0


def test_save_and_list_campaigns(storage):
    storage.save_campaign(SAMPLE_CAMPAIGN, "Campaign A")
    storage.save_campaign(SAMPLE_CAMPAIGN, "Campaign B")
    campaigns = storage.list_campaigns()
    assert len(campaigns) == 2


def test_list_campaigns_returns_summary_fields(storage):
    storage.save_campaign(SAMPLE_CAMPAIGN, "My Campaign")
    campaigns = storage.list_campaigns()
    assert len(campaigns) == 1
    c = campaigns[0]
    assert "id" in c
    assert "name" in c
    assert "created_at" in c
    assert "brand_name" in c


def test_load_campaign(storage):
    campaign_id = storage.save_campaign(SAMPLE_CAMPAIGN, "Loaded Campaign")
    loaded = storage.load_campaign(campaign_id)
    assert loaded is not None
    assert loaded["inputs"]["brand_name"] == "StoreBrand"


def test_load_nonexistent_campaign(storage):
    result = storage.load_campaign("NONEXISTENT")
    assert result is None


def test_delete_campaign(storage):
    campaign_id = storage.save_campaign(SAMPLE_CAMPAIGN, "To Delete")
    result = storage.delete_campaign(campaign_id)
    assert result is True
    assert storage.load_campaign(campaign_id) is None


def test_delete_nonexistent_campaign(storage):
    result = storage.delete_campaign("DOES_NOT_EXIST")
    assert result is False


def test_campaign_count(storage):
    assert storage.campaign_count() == 0
    storage.save_campaign(SAMPLE_CAMPAIGN)
    assert storage.campaign_count() == 1
    storage.save_campaign(SAMPLE_CAMPAIGN)
    assert storage.campaign_count() == 2


def test_clear_all(storage):
    storage.save_campaign(SAMPLE_CAMPAIGN)
    storage.save_campaign(SAMPLE_CAMPAIGN)
    storage.clear_all()
    assert storage.campaign_count() == 0


def test_handles_corrupt_json(tmp_path):
    path = tmp_path / "corrupt.json"
    path.write_text("{ invalid json !!!")
    storage = CampaignStorage(storage_path=str(path))
    # Should not crash; returns empty list
    campaigns = storage.list_campaigns()
    assert campaigns == []


def test_handles_missing_campaigns_key(tmp_path):
    path = tmp_path / "wrong_structure.json"
    path.write_text(json.dumps({"wrong_key": []}))
    storage = CampaignStorage(storage_path=str(path))
    campaigns = storage.list_campaigns()
    assert campaigns == []


def test_most_recent_campaign_is_first(storage):
    id1 = storage.save_campaign(SAMPLE_CAMPAIGN, "First")
    id2 = storage.save_campaign(SAMPLE_CAMPAIGN, "Second")
    campaigns = storage.list_campaigns()
    assert campaigns[0]["id"] == id2
    assert campaigns[1]["id"] == id1


def test_update_campaign_success(storage):
    cid = storage.save_campaign(SAMPLE_CAMPAIGN, "Old Name", status="Draft")
    updated_data = dict(SAMPLE_CAMPAIGN)
    updated_data["brief"] = {"summary": "Updated brief."}
    ok = storage.update_campaign(cid, updated_data, campaign_name="New Name", status="Completed")
    assert ok is True
    loaded = storage.load_campaign(cid)
    assert loaded["brief"]["summary"] == "Updated brief."
    summary = storage.list_campaigns()[0]
    assert summary["name"] == "New Name"
    assert summary["status"] == "Completed"


def test_update_nonexistent_campaign(storage):
    ok = storage.update_campaign("NO_ID", SAMPLE_CAMPAIGN)
    assert ok is False


def test_list_campaigns_filters_and_search(storage):
    camp_a = dict(SAMPLE_CAMPAIGN)
    camp_a["inputs"] = {"brand_name": "Nike", "product_name": "Shoes", "platform": "Instagram Reels"}
    camp_b = dict(SAMPLE_CAMPAIGN)
    camp_b["inputs"] = {"brand_name": "Apple", "product_name": "Watch", "platform": "YouTube Shorts"}
    
    storage.save_campaign(camp_a, "Nike Summer", status="Completed")
    storage.save_campaign(camp_b, "Apple Launch", status="Draft")

    # Search query
    res = storage.list_campaigns(query="nike")
    assert len(res) == 1
    assert res[0]["name"] == "Nike Summer"

    # Platform filter
    res = storage.list_campaigns(platform_filter="YouTube Shorts")
    assert len(res) == 1
    assert res[0]["name"] == "Apple Launch"

    # Status filter
    res = storage.list_campaigns(status_filter="Draft")
    assert len(res) == 1
    assert res[0]["name"] == "Apple Launch"


def test_get_metrics_calculation(storage):
    # Empty metrics
    empty_m = storage.get_metrics()
    assert empty_m["total_campaigns"] == 0
    assert empty_m["avg_quality_score"] is None

    # Populate with scored campaigns
    c1 = dict(SAMPLE_CAMPAIGN)
    c1["quality_review"] = {"overall_score": 80}
    c2 = dict(SAMPLE_CAMPAIGN)
    c2["quality_review"] = {"overall_score": 90}

    storage.save_campaign(c1, "Camp 1", status="Completed")
    storage.save_campaign(c2, "Camp 2", status="Draft")

    metrics = storage.get_metrics()
    assert metrics["total_campaigns"] == 2
    assert metrics["completed_campaigns"] == 1
    assert metrics["draft_campaigns"] == 1
    assert metrics["avg_quality_score"] == 85.0
    assert metrics["total_scored_campaigns"] == 2
