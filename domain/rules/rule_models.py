from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MaterialRouteHints:
    route: str
    needs_model: bool
    modeless: bool
    material: str


@dataclass(frozen=True)
class ManualReviewDecision:
    requires_manual_review: bool
    reason_key: Optional[str] = None
    message: Optional[str] = None
    detail: Optional[str] = None
    return_value: Optional[str] = None


@dataclass(frozen=True)
class DestinationDecision:
    destination_key: str
    route_label_key: str
    is_ai_alias_to_designer: bool = False
