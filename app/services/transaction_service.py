from typing import Any, Dict, List, Literal

import requests

BLOCKSTREAM_MAINNET = "https://blockstream.info/api"
BLOCKSTREAM_TESTNET = "https://blockstream.info/testnet/api"

Network = Literal["mainnet", "testnet"]


def _base_url(network: Network) -> str:
    return BLOCKSTREAM_TESTNET if network == "testnet" else BLOCKSTREAM_MAINNET


def _sats_to_btc(sats: int) -> float:
    return round(sats / 100_000_000, 8)


def fetch_tx_raw(txid: str, network: Network = "mainnet") -> Dict[str, Any]:
    """
    Fetch the raw transaction JSON from Blockstream.
    """
    url = f"{_base_url(network)}/tx/{txid}"
    resp = requests.get(url, timeout=20)
    if resp.status_code == 404:
        raise ValueError("Transaction not found")
    if resp.status_code != 200:
        raise RuntimeError(f"Upstream error from Blockstream: {resp.status_code}")
    return resp.json()


def fetch_tx_status(txid: str, network: Network = "mainnet") -> Dict[str, Any]:
    """
    Fetch the transaction status (confirmed, block_height, block_hash, etc.).
    """
    url = f"{_base_url(network)}/tx/{txid}/status"
    resp = requests.get(url, timeout=20)
    if resp.status_code == 404:
        raise ValueError("Transaction status not found")
    if resp.status_code != 200:
        raise RuntimeError(f"Upstream error from Blockstream: {resp.status_code}")
    return resp.json()


def normalize_transaction(raw_tx: Dict[str, Any], status: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produce a normalized view of a transaction with consistent fields.

    Output shape:
    {
      "txid": str,
      "status": "confirmed" | "unconfirmed",
      "confirmations": int | None,
      "block_height": int | None,
      "fee_btc": float,
      "virtual_size": int | None,
      "inputs": [{"address": str | None, "amount_btc": float}],
      "outputs": [{"address": str | None, "amount_btc": float}],
    }
    """
    # Inputs
    inputs: List[Dict[str, Any]] = []
    for vin in raw_tx.get("vin", []):
        prevout = vin.get("prevout") or {}
        inputs.append(
            {
                "address": prevout.get("scriptpubkey_address"),
                "amount_btc": _sats_to_btc(prevout.get("value", 0)),
            }
        )

    # Outputs
    outputs: List[Dict[str, Any]] = []
    for vout in raw_tx.get("vout", []):
        outputs.append(
            {
                "address": vout.get("scriptpubkey_address"),
                "amount_btc": _sats_to_btc(vout.get("value", 0)),
            }
        )

    # Status and confirmations
    confirmed = bool(status.get("confirmed"))
    block_height = status.get("block_height") if confirmed else None
    # Blockstream does not return confirmations directly; callers may enrich this later
    # using the current chain tip height. For now, leave it as None when unknown.
    confirmations = None
    if confirmed and isinstance(block_height, int) and isinstance(raw_tx.get("status", {}).get("block_height"), int):
        # Some clients embed status in raw_tx; if so, we can compute a placeholder of 1+
        confirmations = 1

    normalized = {
        "txid": raw_tx.get("txid"),
        "status": "confirmed" if confirmed else "unconfirmed",
        "confirmations": confirmations,
        "block_height": block_height,
        "fee_btc": _sats_to_btc(raw_tx.get("fee", 0)),
        "virtual_size": raw_tx.get("vsize"),
        "inputs": inputs,
        "outputs": outputs,
    }
    return normalized


def analyze_transaction(txid: str, network: Network = "mainnet") -> Dict[str, Any]:
    """
    High-level helper that fetches raw data and returns a normalized document.
    """
    raw = fetch_tx_raw(txid, network)
    status = fetch_tx_status(txid, network)
    normalized = normalize_transaction(raw, status)
    return {
        "network": network,
        "source": "blockstream",
        "txid": txid,
        "raw": raw,  # kept for transparency/debugging
        "status": status,
        "normalized": normalized,
    }

