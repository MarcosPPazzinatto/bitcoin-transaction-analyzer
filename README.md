## Overview

**Bitcoin Transaction Analyzer** is a lightweight Python-based tool designed to inspect and analyze Bitcoin transactions in real-time.  
It allows developers, researchers, and blockchain enthusiasts to query any transaction hash and get a detailed breakdown of:

- Inputs and outputs (addresses, amounts, and types)
- Transaction fees and size
- Confirmation status and block height
- Timestamps and related metadata

---

## Features

- Parse and analyze any Bitcoin transaction by hash  
- Fast access using public blockchain APIs (Blockstream, Blockchain.com, or others)  
- Optional Redis cache for repeated queries  
- Built with **Python 3.11+** and **FastAPI** (for REST mode)  
- Modular design that can be extended to other networks (e.g., Testnet, Lightning)

---

## Tech Stack

- **Language:** Python 3.11+
- **Framework:** FastAPI / Typer (for CLI)
- **Cache (optional):** Redis
- **Data Source:** Bitcoin blockchain public APIs

---

## Installation

# Clone the repository
git clone https://github.com/<your-username>/bitcoin-transaction-analyzer.git
cd bitcoin-transaction-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt


## Usage

# Command Line Mode
```
python analyzer.py --tx <transaction_hash>

```

# API Mode

```
uvicorn app.main:app --reload
```
# Then visit:

```
uvicorn app.main:app --reload

```

## Example Output

```
{
  "txid": "f854aeb...",
  "status": "confirmed",
  "confirmations": 18,
  "inputs": [
    {"address": "bc1qxyz...", "amount": 0.0021}
  ],
  "outputs": [
    {"address": "bc1qabcd...", "amount": 0.0019}
  ],
  "fee": 0.0002,
  "block_height": 823001,
  "timestamp": "2025-10-10T12:45:00Z"
}
```

## Contributing

Pull requests are welcome.
If you would like to propose a new feature or fix, please open an issue first to discuss your idea.











