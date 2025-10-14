from typing import Any, Dict, Literal

import requests
from fastapi import FastAPI, HTTPException

app = FastAPI(
    title="Bitcoin Transaction Analyzer",
    description="HTTP API to analyze Bitcoin transactions using public blockchain data sources.",
    version="0.1.0",
)

BLOCKSTREAM_MAINNET = "https://blockstream.info/api"
BLOCKSTREAM_TESTNET = "https://blockstream.info/testnet/api"


def blockstream_base_url(network: Literal["mainnet", "testnet"]) -> str:
    if network == "testnet":
        return BLOCKSTREAM_TESTNET
    return BLOCKSTREAM_MAINNET


def fetch_tx_blockstream(txid: str, network: Literal["mainnet", "testnet"]) -> Dict[str, Any]:
    base = blockstream_base_url(network)
    url = f"{base}/tx/{txid}"
    resp = requests.get(url, timeout=20)
    if resp.status_code == 404:
        raise HTTPException(status_code=404, detail="Transaction not found")
    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Upstream error from Blockstream: {resp.status_code}")
    return resp.json()


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/tx/{txid}")
def get_transaction(
    txid: str,
    network: Literal["mainnet", "testnet"] = "mainnet",
) -> Dict[str, Any]:
    """
    Return raw transaction details from Blockstream for the given txid.

    Examples:
      - Mainnet:  GET /tx/<txid>
      - Testnet:  GET /tx/<txid>?network=testnet
    """
    data = fetch_tx_blockstream(txid, network)
    # The response is already well-structured JSON from Blockstream.
    # You may normalize/reshape fields here in the future.
    return {
        "network": network,
        "txid": txid,
        "source": "blockstream",
        "data": data,
    }

