import asyncio
import os
import random
import string
from typing import Dict, Tuple

import requests
from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from xrpl.wallet import Wallet

# Main wallets for collecting payments
WALLETS = {
    'ETH': '0x2e289604653397ddc18800192e54365423e440c9',
    'SOL': '8xJhZZuW6VJxU9byVjtR91vPospbaujEtW6M4EPNXo6B',
    'BTC': 'bc1qh34k6k6lj2w55h8tzwxv6qyuqsxexj3tg7vr0p',
    'XRP': 'rnyo5DMAdnCTefv4BCjRzgGykP9f8id8sw',
    'LTC': 'ltc1qc4zrtukr6kn9yu7jvvvcfnh88mmw8d4m0g4s5u',
}

BLOCKCYPHER_TOKEN = os.environ.get('BLOCKCYPHER_TOKEN')

# Internal invoice storage
_INVOICES: Dict[str, Dict] = {}


def _generate_id(currency: str) -> str:
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{currency}_{suffix}"


async def _http_get(url: str) -> requests.Response:
    return await asyncio.to_thread(requests.get, url)


async def _http_post(url: str) -> requests.Response:
    return await asyncio.to_thread(requests.post, url)


async def _create_blockcypher_address(coin: str) -> Dict[str, str]:
    url = f"https://api.blockcypher.com/v1/{coin}/main/addrs"
    if BLOCKCYPHER_TOKEN:
        url += f"?token={BLOCKCYPHER_TOKEN}"
    resp = await _http_post(url)
    resp.raise_for_status()
    return resp.json()


async def _create_sol_address() -> Dict[str, str]:
    kp = Keypair.generate()
    return {"private": kp.secret_key.hex(), "address": str(kp.public_key)}


async def _create_xrp_address() -> Dict[str, str]:
    wallet = Wallet.create()
    return {"private": wallet.seed, "address": wallet.classic_address}


async def create_invoice(amount: float, currency: str) -> Tuple[str, str]:
    """Generate a unique address for the invoice."""
    currency = currency.upper()
    invoice_id = _generate_id(currency)

    if currency in ("BTC", "ETH", "LTC"):
        coin_map = {"BTC": "btc", "ETH": "eth", "LTC": "ltc"}
        data = await _create_blockcypher_address(coin_map[currency])
        address = data["address"]
        private = data["private"]
    elif currency == "SOL":
        wallet = await _create_sol_address()
        address = wallet["address"]
        private = wallet["private"]
    elif currency == "XRP":
        wallet = await _create_xrp_address()
        address = wallet["address"]
        private = wallet["private"]
    else:
        raise ValueError("Unsupported currency")

    _INVOICES[invoice_id] = {
        "amount": float(amount),
        "currency": currency,
        "address": address,
        "private": private,
        "paid": False,
        "forwarded": False,
    }
    return invoice_id, address


async def _check_blockcypher(currency: str, address: str) -> float:
    coin_map = {"BTC": "btc", "ETH": "eth", "LTC": "ltc"}
    url = f"https://api.blockcypher.com/v1/{coin_map[currency]}/main/addrs/{address}/balance"
    if BLOCKCYPHER_TOKEN:
        url += f"?token={BLOCKCYPHER_TOKEN}"
    resp = await _http_get(url)
    resp.raise_for_status()
    data = resp.json()
    bal = data.get("final_balance", 0) + data.get("unconfirmed_balance", 0)
    if currency == "ETH":
        return bal / 1e18
    return bal / 1e8


async def _check_sol(address: str) -> float:
    async with AsyncClient("https://api.mainnet-beta.solana.com") as client:
        res = await client.get_balance(address)
        lamports = res.get("result", {}).get("value", 0)
        return lamports / 1e9


async def _check_xrp(address: str) -> float:
    resp = await _http_get(f"https://xrpscan.com/api/v1/account/{address}")
    if resp.status_code == 200:
        data = resp.json()
        try:
            return float(data.get("balance", 0))
        except (TypeError, ValueError):
            return 0.0
    return 0.0


async def check_transaction_status(invoice_id: str) -> str | None:
    """Check blockchain for payment confirmation."""
    invoice = _INVOICES.get(invoice_id)
    if not invoice:
        return None

    if invoice["paid"]:
        return "paid"

    currency = invoice["currency"]
    address = invoice["address"]
    amount = invoice["amount"]

    if currency in ("BTC", "ETH", "LTC"):
        balance = await _check_blockcypher(currency, address)
    elif currency == "SOL":
        balance = await _check_sol(address)
    elif currency == "XRP":
        balance = await _check_xrp(address)
    else:
        return None

    if balance >= amount:
        invoice["paid"] = True
        return "paid"
    return "pending"
