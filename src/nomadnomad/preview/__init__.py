"""本地预览与演示辅助（非 API 契约的一部分）。"""

from nomadnomad.preview.fake_llm_clients import FixedJsonClient, RecordingSequentialJsonClient, SequentialJsonClient
from nomadnomad.preview.snapshot_contract_bridge import (
    example_proposal_payload_from_snapshot,
    requirement_payload_from_snapshot,
)

__all__ = [
    "FixedJsonClient",
    "RecordingSequentialJsonClient",
    "example_proposal_payload_from_snapshot",
    "requirement_payload_from_snapshot",
    "SequentialJsonClient",
]
