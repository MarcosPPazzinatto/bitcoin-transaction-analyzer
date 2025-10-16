import json
import re
import types
from typing import Any, Dict

import pytest

# Import the high-level analyzer
from app.services.transaction_service import analyze_transaction


class FakeResponse:
    def __init__(self, status_code: int, payload: Dict[str, Any]):
        self.status_code = status_code
        self._payload = payload

    def json(self) -> Dict[str, Any]:
        return self._payload


def make_mock_requests_get(success_tx_payload: Dict[str, Any], success_status_payload: Dict[str, Any]):
    """
    Returns a function that mimics requests.get behavior for:
      - .../tx/<txid>
      - .../tx/<txid>/status
    """
    def _mock_get(url: str, timeout: int = 20, *args, **kwargs):
        # Match endpoints
        tx_match = re.search(r"/tx/([0-9a-fA-F]+)$", url)
        status_match = re.search(r"/tx/([0-9a-fA-F]+)/status$", url)

        # Success cases
        if tx_match:
            return FakeResponse(200, success_tx_payload)
        if status_match:
            return FakeResponse(200, success_status_payload)

        # Default: simulate upstream error for unexpected URLs
        return FakeResponse(500, {"error": "unexpected URL"})
    return _mock_get


def test_analyze_transaction_success(monkeypatch):
    """
    Happy path: verifies the normalized shape and key fields.
    """
    txid = "f" * 64

    # Minimal but realistic raw tx payload from Blockstream
    raw_tx = {
        "txid": txid,
        "fee": 200,         # sats
        "vsize": 141,
        "vin": [
            {"prevout": {"value": 210000, "scriptpubkey_address": "bc1qinputaddr..."}}
        ],
        "vout": [
            {"value": 190000, "scriptpubkey_address": "bc1qoutput1..."},
            {"value": 19900,  "scriptpubkey_address": "bc1qchange..."}
        ],
    }

    # Status payload
    status = {
        "confirmed": True,
        "block_height": 823001,
        "block_hash": "abc123",
    }

    mock_get = make_mock_requests_get(raw_tx, status)

    # Patch requests.get used inside the service
    import requests
    monkeypatch.setattr(requests, "get", mock_get)

    result = analyze_transaction(txid, network="mainnet")

    # Basic structure
    assert result["network"] == "mainnet"
    assert result["source"] == "blockstream"
    assert result["txid"] == txid

    # Normalized section
    norm = result["normalized"]
    assert norm["txid"] == txid
    assert norm["status"] == "confirmed"
    assert norm["block_height"] == 823001
    # confirmations is None or >= 1 depending on available data; we allow either
    assert "confirmations" in norm

    # Fee conversion from sats to BTC
    assert norm["fee_btc"] == 0.000002  # 200 sats

    # Inputs normalization
    assert isinstance(norm["inputs"], list) and len(norm["inputs"]) == 1
    assert norm["inputs"][0]["address"] == "bc1qinputaddr..."
    assert norm["inputs"][0]["amount_btc"] == 0.0021  # 210000 sats

    # Outputs normalization
    assert isinstance(norm["outputs"], list) and len(norm["outputs"]) == 2
    assert norm["outputs"][0]["address"] == "bc1qoutput1..."
    assert norm["outputs"][0]["amount_btc"] == 0.0019  # 190000 sats
    assert norm["outputs"][1]["address"] == "bc1qchange..."
    assert norm["outputs"][1]["amount_btc"] == 0.000199  # 19900 sats

    # Raw and status are preserved for transparency
    assert result["raw"]["txid"] == txid
    assert result["status"]["confirmed"] is True


def test_analyze_transaction_not_found(monkeypatch):
    """
    404 from Blockstream should surface as ValueError.
    """
    txid = "e" * 64

    def _mock_get(url: str, timeout: int = 20, *args, **kwargs):
        if url.endswith(f"/tx/{txid}") or url.endswith(f"/tx/{txid}/status"):
            return FakeResponse(404, {"error": "not found"})
        return FakeResponse(500, {"error": "unexpected URL"})

    import requests
    monkeypatch.setattr(requests, "get", _mock_get)

    with pytest.raises(ValueError):
        analyze_transaction(txid, network="mainnet")


def test_analyze_transaction_upstream_error(monkeypatch):
    """
    Non-200/404 upstream responses should raise RuntimeError.
    """
    txid = "d" * 64

    def _mock_get(url: str, timeout: int = 20, *args, **kwargs):
        # Simulate a 503 from upstream
        return FakeResponse(503, {"error": "service unavailable"})

    import requests
    monkeypatch.setattr(requests, "get", _mock_get)

    with pytest.raises(RuntimeError):
        analyze_transaction(txid, network="mainnet")

