import os
import random
import string
from typing import Dict, Tuple

import asyncio
import requests
from web3 import Web3
from eth_account import Account
from solana.keypair import Keypair
from solana.rpc.async_api import AsyncClient
from xrpl.wallet import Wallet
from xrpl.clients import JsonRpcClient
from xrpl.models.requests.account_info import AccountInfo
from xrpl.models.transactions import Payment
from xrpl.transaction import safe_sign_and_submit_transaction, send_reliable_submission


# RPC endpoints for self-hosted nodes
ETH_NODE_URL = os.getenv("ETH_NODE_URL", "http://localhost:8545")
SOL_NODE_URL = os.getenv("SOL_NODE_URL", "http://localhost:8899")
BTC_RPC_URL = os.getenv("BTC_RPC_URL", "http://user:pass@127.0.0.1:8332")
LTC_RPC_URL = os.getenv("LTC_RPC_URL", "http://user:pass@127.0.0.1:9332")
XRP_RPC_URL = os.getenv("XRP_RPC_URL", "http://localhost:5005")

# Destination wallets
WALLETS: Dict[str, str] = {
    "ETH": "0x2e289604653397ddc18800192e54365423e440c9",
    "SOL": "8xJhZZuW6VJxU9byVjtR91vPospbaujEtW6M4EPNXo6B",
    "BTC": "bc1qh34k6k6lj2w55h8tzwxv6qyuqsxexj3tg7vr0p",
    "XRP": "rnyo5DMAdnCTefv4BCjRzgGykP9f8id8sw",
    "LTC": "ltc1qc4zrtukr6kn9yu7jvvvcfnh88mmw8d4m0g4s5u",
}

# Invoice storage used by the bot
_INVOICES: Dict[str, Dict] = {}


# ---- Helpers ---------------------------------------------------------------

def _generate_id(currency: str) -> str:
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{currency}_{suffix}"


def _rpc_call(url: str, method: str, params=None):
    payload = {"jsonrpc": "1.0", "id": "rpc", "method": method, "params": params or []}
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    data = resp.json()
    if data.get("error"):
        raise RuntimeError(data["error"])
    return data["result"]


def _sweep_utxos(rpc_url: str, from_addr: str, dest_addr: str) -> str | None:
    """Create and broadcast a transaction spending all UTXOs for from_addr."""
    utxos = _rpc_call(rpc_url, "listunspent", [1, 9999999, [from_addr]])
    if not utxos:
        return None
    inputs = [{"txid": u["txid"], "vout": u["vout"]} for u in utxos]
    total = sum(u["amount"] for u in utxos)
    psbt_resp = _rpc_call(
        rpc_url,
        "walletcreatefundedpsbt",
        [inputs, {dest_addr: total}, 0, {"subtractFeeFromOutputs": [0]}],
    )
    psbt = psbt_resp["psbt"]
    processed = _rpc_call(rpc_url, "walletprocesspsbt", [psbt])
    final = _rpc_call(rpc_url, "finalizepsbt", [processed["psbt"]])
    if not final.get("complete"):
        return None
    txid = _rpc_call(rpc_url, "sendrawtransaction", [final["hex"]])
    return txid


# ---- Address Generation ----------------------------------------------------

async def _create_eth_address() -> Dict[str, str]:
    acct = Account.create()
    return {"private": acct.key.hex(), "address": acct.address}


async def _create_sol_address() -> Dict[str, str]:
    kp = Keypair.generate()
    return {"private": kp.secret_key.hex(), "address": str(kp.public_key)}


async def _create_btc_address(label: str) -> Dict[str, str]:
    address = _rpc_call(BTC_RPC_URL, "getnewaddress", [label])
    return {"private": "node", "address": address}


async def _create_ltc_address(label: str) -> Dict[str, str]:
    address = _rpc_call(LTC_RPC_URL, "getnewaddress", [label])
    return {"private": "node", "address": address}


async def _create_xrp_address() -> Dict[str, str]:
    wallet = Wallet.create()
    return {"private": wallet.seed, "address": wallet.classic_address}


# ---- Public API ------------------------------------------------------------

async def create_invoice(amount: float, currency: str) -> Tuple[str, str]:
    """Create a deposit address for the given currency."""
    currency = currency.upper()
    invoice_id = _generate_id(currency)

    if currency == "ETH":
        data = await _create_eth_address()
    elif currency == "SOL":
        data = await _create_sol_address()
    elif currency == "BTC":
        data = await _create_btc_address(invoice_id)
    elif currency == "LTC":
        data = await _create_ltc_address(invoice_id)
    elif currency == "XRP":
        data = await _create_xrp_address()
    else:
        raise ValueError("Unsupported currency")

    _INVOICES[invoice_id] = {
        "amount": float(amount),
        "currency": currency,
        "address": data["address"],
        "private": data["private"],
        "paid": False,
        "forwarded": False,
    }
    return invoice_id, data["address"]


# ---- Balance checking ------------------------------------------------------

async def _check_eth(address: str) -> float:
    w3 = Web3(Web3.HTTPProvider(ETH_NODE_URL))
    bal = await asyncio.to_thread(w3.eth.get_balance, address)
    return bal / 10**18


async def _check_sol(address: str) -> float:
    async with AsyncClient(SOL_NODE_URL) as client:
        res = await client.get_balance(address)
        return res.get("result", {}).get("value", 0) / 10**9


async def _check_btc(address: str) -> float:
    return float(_rpc_call(BTC_RPC_URL, "getreceivedbyaddress", [address, 1]))


async def _check_ltc(address: str) -> float:
    return float(_rpc_call(LTC_RPC_URL, "getreceivedbyaddress", [address, 1]))


async def _check_xrp(address: str) -> float:
    client = JsonRpcClient(XRP_RPC_URL)
    req = AccountInfo(account=address, ledger_index="validated")
    resp = client.request(req)
    if resp.is_successful() and resp.result.get("account_data"):
        bal = int(resp.result["account_data"].get("Balance", 0))
        return bal / 1_000_000
    return 0.0


async def check_transaction_status(invoice_id: str) -> str | None:
    invoice = _INVOICES.get(invoice_id)
    if not invoice:
        return None

    if invoice["paid"]:
        return "paid"

    address = invoice["address"]
    currency = invoice["currency"]
    amount = invoice["amount"]

    if currency == "ETH":
        bal = await _check_eth(address)
    elif currency == "SOL":
        bal = await _check_sol(address)
    elif currency == "BTC":
        bal = await _check_btc(address)
    elif currency == "LTC":
        bal = await _check_ltc(address)
    elif currency == "XRP":
        bal = await _check_xrp(address)
    else:
        return None

    if bal >= amount:
        invoice["paid"] = True
        return "paid"
    return "pending"


# ---- Auto forwarding -------------------------------------------------------

async def forward_funds(invoice_id: str) -> bool:
    invoice = _INVOICES.get(invoice_id)
    if not invoice or not invoice.get("paid") or invoice.get("forwarded"):
        return False

    currency = invoice["currency"]
    address = invoice["address"]
    private = invoice["private"]
    destination = WALLETS[currency]

    if currency == "ETH":
        w3 = Web3(Web3.HTTPProvider(ETH_NODE_URL))
        nonce = w3.eth.get_transaction_count(address)
        gas_price = w3.eth.gas_price
        value = w3.eth.get_balance(address) - gas_price * 21000
        tx = {
            "to": destination,
            "value": value,
            "gas": 21000,
            "gasPrice": gas_price,
            "nonce": nonce,
            "chainId": w3.eth.chain_id,
        }
        signed = w3.eth.account.sign_transaction(tx, private)
        w3.eth.send_raw_transaction(signed.rawTransaction)

    elif currency == "SOL":
        async with AsyncClient(SOL_NODE_URL) as client:
            balance_resp = await client.get_balance(address)
            lamports = balance_resp.get("result", {}).get("value", 0)
            from solana.transaction import Transaction
            from solana.system_program import TransferParams, transfer
            kp = Keypair.from_secret_key(bytes.fromhex(private))
            txn = Transaction()
            txn.add(transfer(TransferParams(from_pubkey=kp.public_key, to_pubkey=destination, lamports=lamports - 5000)))
            txn.sign(kp)
            await client.send_transaction(txn, kp)

    elif currency == "BTC":
        txid = _sweep_utxos(BTC_RPC_URL, address, destination)
        if not txid:
            return False

    elif currency == "LTC":
        txid = _sweep_utxos(LTC_RPC_URL, address, destination)
        if not txid:
            return False

    elif currency == "XRP":
        client = JsonRpcClient(XRP_RPC_URL)
        wallet = Wallet(seed=private, sequence=0)
        balance = await _check_xrp(address)
        payment = Payment(account=wallet.classic_address,
                          destination=destination,
                          amount=str(int(balance * 1_000_000)))
        safe_sign_and_submit_transaction(payment, wallet, client)
        send_reliable_submission(payment, client)

    else:
        return False

    invoice["forwarded"] = True
    return True
