import requests
from bot.misc.env import EnvKeys

BASE_URL = 'https://shkeeper.io/api/v1'


async def create_invoice(amount: float, currency: str):
    payload = {
        'merchant_id': EnvKeys.SHK_MERCHANT_ID,
        'api_key': EnvKeys.SHK_API_KEY,
        'amount': amount,
        'currency': currency.upper(),
    }
    response = requests.post(f'{BASE_URL}/invoice', json=payload, timeout=10)
    response.raise_for_status()
    data = response.json()
    invoice_id = str(data.get('id'))
    url = data.get('payment_url') or data.get('url') or data.get('address')
    return invoice_id, url


async def check_transaction_status(invoice_id: str):
    params = {
        'merchant_id': EnvKeys.SHK_MERCHANT_ID,
        'api_key': EnvKeys.SHK_API_KEY,
    }
    response = requests.get(f'{BASE_URL}/invoice/{invoice_id}', params=params, timeout=10)
    response.raise_for_status()
    data = response.json()
    return data.get('status')
