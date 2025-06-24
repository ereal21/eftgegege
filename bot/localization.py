LANGUAGES = {
    'en': {
        'hello': '👋 Hello, {user}!',
        'balance': '💰 Balance: {balance} EUR',
        'basket': '🛒 Basket: {items} item(s)',
        'overpay': '💳 Send the exact amount. Overpayments will be credited.',
        'shop': '🛍 Shop',
        'profile': '👤 Profile',
        'top_up': '💸 Top Up',
        'channel': '📢 Channel',
        'support': '🆘 Support',
        'language': '🌐 Language',
        'admin_panel': '🎛 Admin Panel',
        'choose_language': 'Please choose a language',
    },
    'ru': {
        'hello': '👋 Привет, {user}!',
        'balance': '💰 Баланс: {balance} EUR',
        'basket': '🛒 Корзина: {items} шт.',
        'overpay': '💳 Отправьте точную сумму. Переплаты будут зачислены.',
        'shop': '🛍 Магазин',
        'profile': '👤 Профиль',
        'top_up': '💸 Пополнить',
        'channel': '📢 Канал',
        'support': '🆘 Поддержка',
        'language': '🌐 Язык',
        'admin_panel': '🎛 Админ панель',
        'choose_language': 'Пожалуйста, выберите язык',
    },
    'lt': {
        'hello': '👋 Sveiki, {user}!',
        'balance': '💰 Balansas: {balance} EUR',
        'basket': '🛒 Krepšelis: {items} prekės',
        'overpay': '💳 Siųskite tikslią sumą. Permokos bus įskaitytos.',
        'shop': '🛍 Parduotuvė',
        'profile': '👤 Profilis',
        'top_up': '💸 Papildyti',
        'channel': '📢 Kanalu',
        'support': '🆘 Pagalba',
        'language': '🌐 Kalba',
        'admin_panel': '🎛 Admin pultas',
        'choose_language': 'Pasirinkite kalbą',
    },
}

def t(lang: str, key: str, **kwargs) -> str:
    lang_data = LANGUAGES.get(lang, LANGUAGES['en'])
    template = lang_data.get(key, '')
    return template.format(**kwargs)
