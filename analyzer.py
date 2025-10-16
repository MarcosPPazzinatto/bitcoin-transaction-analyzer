# analyzer.py (replace previous simple version)
import json
import typer
from typing import Any

from app.services.transaction_service import analyze_transaction

app = typer.Typer(help="Analyze Bitcoin transactions using public blockchain APIs.")


@app.command()
def analyze(tx: str, network: str = "mainnet") -> None:
    """
    Analyze a Bitcoin transaction by hash.

    Example:
        python analyzer.py analyze --tx <transaction_hash> --network mainnet
    """
    result: Any = analyze_transaction(tx, network)  # returns normalized + raw
    typer.echo(json.dumps(result, indent=2))


if __name__ == "__main__":
    app()

