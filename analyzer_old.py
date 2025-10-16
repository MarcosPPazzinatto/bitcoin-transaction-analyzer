import requests
import typer
import json
from typing import Any, Dict

app = typer.Typer(help="Analyze Bitcoin transactions using public blockchain APIs.")

BLOCKSTREAM_API = "https://blockstream.info/api"


def fetch_transaction(txid: str) -> Dict[str, Any]:
    """Fetch transaction details from Blockstream API."""
    url = f"{BLOCKSTREAM_API}/tx/{txid}"
    response = requests.get(url)

    if response.status_code != 200:
        typer.echo(f"Error fetching transaction: {response.status_code}")
        raise typer.Exit(code=1)

    return response.json()


@app.command()
def analyze(tx: str):
    """
    Analyze a Bitcoin transaction by hash.
    Example:
        python analyzer.py analyze --tx <transaction_hash>
    """
    typer.echo(f"Fetching transaction data for: {tx}\n")

    data = fetch_transaction(tx)
    typer.echo(json.dumps(data, indent=2))


if __name__ == "__main__":
    app()

