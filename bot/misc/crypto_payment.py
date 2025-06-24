import asyncio
import random
import string
from typing import Dict

# Main wallets for collecting payments
WALLETS = {
    'ETH': '0x2e289604653397ddc18800192e54365423e440c9',
    'SOL': '8xJhZZuW6VJxU9byVjtR91vPospbaujEtW6M4EPNXo6B',
    'BTC': 'bc1qh34k6k6lj2w55h8tzwxv6qyuqsxexj3tg7vr0p',
    'XRP': 'rnyo5DMAdnCTefv4BCjRzgGykP9f8id8sw',
    'LTC': 'ltc1qc4zrtukr6kn9yu7jvvvcfnh88mmw8d4m0g4s5u',
}

# Internal invoice storage
_INVOICES: Dict[str, Dict] = {}


async def _auto_confirm(invoice_id: str) -> None:
    """Simulate blockchain confirmation."""
    await asyncio.sleep(5)
    invoice = _INVOICES.get(invoice_id)
    if invoice:
        invoice['paid'] = True


async def create_invoice(amount: float, currency: str):
    """Create a new invoice with unique address."""
    currency = currency.upper()
    invoice_id = f"{currency}_{random.randint(100000, 999999)}"
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    address = f"{WALLETS[currency]}_{suffix}"
    _INVOICES[invoice_id] = {
        'amount': amount,
        'currency': currency,
        'address': address,
        'paid': False,
        'forwarded': False,
    }
    asyncio.create_task(_auto_confirm(invoice_id))
    return invoice_id, address


async def _forward_funds(currency: str, address: str) -> None:
    """Placeholder for forwarding funds to main wallet."""
    await asyncio.sleep(0)


async def check_transaction_status(invoice_id: str):
    """Return transaction status and forward funds when paid."""
    invoice = _INVOICES.get(invoice_id)
    if not invoice:
        return None
    if invoice['paid'] and not invoice['forwarded']:
        await _forward_funds(invoice['currency'], invoice['address'])
        invoice['forwarded'] = True
    return 'paid' if invoice['paid'] else 'pending'
