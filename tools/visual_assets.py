"""Visual assets tool: classify a fake visual asset.

This is a governed *adapter* to an external vision service. It does NOT run a
real model and adds no CV dependencies (no torch / torchvision) to this repo.
In a production system this function would call out to a separate PyTorch
vision service; here it returns fake, pre-computed classification metadata so
the governance flow (permissions, risk, audit) can be demonstrated end to end.
"""
from typing import Any, Dict

from tools import load_data


def classify_visual_asset(asset_id: str) -> Dict[str, Any]:
    """Return classification metadata for a fake visual asset.

    Looks up ``asset_id`` in the fake catalog and returns the structured
    classification result. If the asset is not found, a clear error object is
    returned rather than raising, so the gateway can log and pass it back safely.
    """
    assets = load_data("visual_assets.json")
    for asset in assets:
        if asset.get("asset_id") == asset_id:
            return {
                "asset_id": asset["asset_id"],
                "filename": asset["filename"],
                "description": asset["description"],
                "predicted_class": asset["predicted_class"],
                "confidence": asset["confidence"],
                "visual_tags": asset["visual_tags"],
                "model_source": asset["model_source"],
            }

    return {
        "error": "asset_not_found",
        "asset_id": asset_id,
        "model_source": "simulated_pytorch_vision_service",
    }
