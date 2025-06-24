import datetime
import os

from aiogram import Dispatcher
from aiogram.types import Message, CallbackQuery
from aiogram.utils.exceptions import ChatNotFound

from bot.database.methods import check_role, select_today_users, select_admins, get_user_count, select_today_orders, \
    select_all_orders, select_today_operations, select_users_balance, select_all_operations, select_count_items, \
    select_count_goods, select_count_categories, select_count_bought_items, check_category, create_category, \
    delete_category, update_category, check_item, create_item, add_values_to_item, update_item, \
    delete_item, check_value, delete_only_items, select_bought_item
from bot.utils.files import get_next_file_path
from bot.database.models import Permission
from bot.handlers.other import get_bot_user_ids
from bot.keyboards import shop_management, goods_management, categories_management, back, item_management, \
    question_buttons
from bot.logger_mesh import logger
from bot.misc import TgConfig


async def shop_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        await bot.edit_message_text('⛩️ Shop management menu',
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=shop_management())
        return
    await call.answer('Insufficient rights')


async def logs_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    role = check_role(user_id)
    file_path = 'bot.log'
    if role >= Permission.SHOP_MANAGE:
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            with open(file_path, 'rb') as document:
                await bot.send_document(chat_id=call.message.chat.id,
                                        document=document)
                return
        else:
            await call.answer(text="❗️ Kolkas nėra logų")
            return
    await call.answer('Insufficient rights')


async def goods_management_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        await bot.edit_message_text('🛒 Prekių valdymo meniu',
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=goods_management())
        return
    await call.answer('Insufficient rights')


async def categories_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        await bot.edit_message_text('🧾 Kategorijų valdymo meniu',
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=categories_management())
        return
    await call.answer('Insufficient rights')


async def add_category_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = 'add_category'
    TgConfig.STATE[f'{user_id}_message_id'] = call.message.message_id
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        await bot.edit_message_text('Enter category name',
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=back("categories_management"))
        return
    await call.answer('Insufficient rights')


async def add_subcategory_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = 'add_subcategory_parent'
    TgConfig.STATE[f'{user_id}_message_id'] = call.message.message_id
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        await bot.edit_message_text('Enter parent category name',
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=back("categories_management"))
        return
    await call.answer('Insufficient rights')


async def statistics_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        await bot.edit_message_text('Shop statistics:\n'
                                    '➖➖➖➖➖➖➖➖➖➖➖➖➖\n'
                                    '<b>◽USERS</b>\n'
                                    f'◾️Users in last 24h: {select_today_users(today)}\n'
                                    f'◾️Total administrators: {select_admins()}\n'
                                    f'◾️Total users: {get_user_count()}\n'
                                    '➖➖➖➖➖➖➖➖➖➖➖➖➖\n'
                                    '◽<b>FUNDS</b>\n'
                                    f'◾Sales in 24h: {select_today_orders(today)}€\n'
                                    f'◾Items sold for: {select_all_orders()}€\n'
                                    f'◾Top-ups in 24h: {select_today_operations(today)}€\n'
                                    f'◾Funds in system: {select_users_balance()}€\n'
                                    f'◾Total topped up: {select_all_operations()}€\n'
                                    '➖➖➖➖➖➖➖➖➖➖➖➖➖\n'
                                    '◽<b>OTHER</b>\n'
                                    f'◾Items: {select_count_items()}pcs.\n'
                                    f'◾Positions: {select_count_goods()}pcs.\n'
                                    f'◾Categories: {select_count_categories()}pcs.\n'
                                    f'◾Items sold: {select_count_bought_items()}pcs.',
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=back('shop_management'),
                                    parse_mode='HTML')
        return
    await call.answer('Insufficient rights')


async def process_category_for_add(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    msg = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    TgConfig.STATE[user_id] = None
    category = check_category(msg)
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    if category:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='❌ Category not created (already exists)',
                                    reply_markup=back('categories_management'))
        return
    create_category(msg)
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='✅ Category created',
                                reply_markup=back('categories_management'))
    admin_info = await bot.get_chat(user_id)
    logger.info(f"User {user_id} ({admin_info.first_name}) "
                f'created new category "{msg}"')


async def process_subcategory_parent(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    parent = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    TgConfig.STATE[user_id] = 'add_subcategory_name'
    TgConfig.STATE[f'{user_id}_parent'] = parent
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    if not check_category(parent):
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='❌ Parent category does not exist',
                                    reply_markup=back('categories_management'))
        TgConfig.STATE[user_id] = None
        return
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='Enter subcategory name',
                                reply_markup=back('categories_management'))


async def process_subcategory_name(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    sub = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    parent = TgConfig.STATE.get(f'{user_id}_parent')
    TgConfig.STATE[user_id] = None
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    if check_category(sub):
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='❌ Subcategory already exists',
                                    reply_markup=back('categories_management'))
        return
    create_category(sub, parent)
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='✅ Subcategory created',
                                reply_markup=back('categories_management'))
    admin_info = await bot.get_chat(user_id)
    logger.info(f"User {user_id} ({admin_info.first_name}) "
                f'created subcategory "{sub}" under "{parent}"')


async def delete_category_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = 'delete_category'
    TgConfig.STATE[f'{user_id}_message_id'] = call.message.message_id
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        await bot.edit_message_text('Enter category name',
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=back("categories_management"))
        return
    await call.answer('Insufficient rights')


async def process_category_for_delete(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    msg = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    TgConfig.STATE[user_id] = None
    category = check_category(msg)
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    if not category:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='❌ Category not deleted (does not exist)',
                                    reply_markup=back('categories_management'))
        return
    delete_category(msg)
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='✅ Category deleted',
                                reply_markup=back('categories_management'))
    admin_info = await bot.get_chat(user_id)
    logger.info(f"User {user_id} ({admin_info.first_name}) "
                f'deleted category "{category["name"]}"')


async def update_category_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[f'{user_id}_message_id'] = call.message.message_id
    TgConfig.STATE[user_id] = 'check_category'
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        await bot.edit_message_text('Enter category name to update:',
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=back("categories_management"))
        return
    await call.answer('Insufficient rights')


async def check_category_for_update(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    category_name = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    category = check_category(category_name)
    if not category:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='❌ Category cannot be updated (does not exist)',
                                    reply_markup=back('categories_management'))
        return
    TgConfig.STATE[user_id] = 'update_category_name'
    TgConfig.STATE[f'{user_id}_check_category'] = message.text
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='Enter new category name:',
                                reply_markup=back('categories_management'))


async def check_category_name_for_update(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    category = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    old_name = TgConfig.STATE.get(f'{user_id}_check_category')
    TgConfig.STATE[user_id] = None
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    update_category(old_name, category)
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text=f'✅ Category "{category}" updated successfully.',
                                reply_markup=back('categories_management'))
    admin_info = await bot.get_chat(user_id)
    logger.info(f"User {user_id} ({admin_info.first_name}) "
                f'changed category "{old_name}" to "{category}"')


async def goods_settings_menu_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = None
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        await bot.edit_message_text('🛒 Pasirinkite veiksmą šiai prekei',
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=item_management())
        return
    await call.answer('Insufficient rights')


async def add_item_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[f'{user_id}_message_id'] = call.message.message_id
    TgConfig.STATE[user_id] = 'create_item_name'
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        await bot.edit_message_text('🏷️ Įveskite prekės pavadinimą',
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=back("item-management"))
        return
    await call.answer('Insufficient rights')


async def check_item_name_for_add(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    item_name = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    item = check_item(item_name)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    if item:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='❌ Item cannot be created (already exists)',
                                    reply_markup=back('item-management'))
        return
    TgConfig.STATE[user_id] = 'create_item_description'
    TgConfig.STATE[f'{user_id}_name'] = message.text
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='Enter description for item:',
                                reply_markup=back('item-management'))


async def add_item_description(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    TgConfig.STATE[f'{user_id}_description'] = message.text
    TgConfig.STATE[user_id] = 'create_item_price'
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='Enter price for item:',
                                reply_markup=back('item-management'))


async def add_item_price(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    if not message.text.isdigit():
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='⚠️ Invalid price value.',
                                    reply_markup=back('item-management'))
        return
    TgConfig.STATE[user_id] = 'check_item_category'
    TgConfig.STATE[f'{user_id}_price'] = message.text
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='Введите категорию, к которой будет относится позиция:',
                                reply_markup=back('item-management'))


async def check_category_for_add_item(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    category_name = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    category = check_category(category_name)
    if not category:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='❌ Item cannot be created (invalid category)',
                                    reply_markup=back('item-management'))
        return
    TgConfig.STATE[user_id] = None
    TgConfig.STATE[f'{user_id}_category'] = category_name
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='Will this item have unlimited goods? '
                                     '(every user will receive the same copy)',
                                reply_markup=question_buttons('infinity', 'item-management'))


async def adding_value_to_position(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    answer = call.data.split('_')[1]
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    TgConfig.STATE[user_id] = 'add_item_value'
    TgConfig.STATE[f'{user_id}_answer'] = answer
    if answer == 'no':
        await bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=message_id,
                                    text='Enter items for the position separated by ;:',
                                    reply_markup=back('item-management'))
    else:
        await bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=message_id,
                                    text='Enter item value:',
                                    reply_markup=back('item-management'))


async def adding_item(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    TgConfig.STATE[user_id] = None
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    item_name = TgConfig.STATE.get(f'{user_id}_name')
    item_description = TgConfig.STATE.get(f'{user_id}_description')
    item_price = TgConfig.STATE.get(f'{user_id}_price')
    category_name = TgConfig.STATE.get(f'{user_id}_category')
    answer = TgConfig.STATE.get(f'{user_id}_answer')
    if answer == 'no':
        if message.photo:
            file_path = get_next_file_path(item_name)

            file_path = get_next_file_path(item_name)

            file_name = f"{item_name}_{int(datetime.datetime.now().timestamp())}.jpg"
            file_path = os.path.join('assets', 'uploads', file_name)


            await message.photo[-1].download(destination_file=file_path)
            values_list = [file_path]
        else:
            values_list = message.text.split(';')
        await bot.delete_message(chat_id=message.chat.id,
                                 message_id=message.message_id)
        create_item(item_name, item_description, item_price, category_name)
        for i in values_list:
            add_values_to_item(item_name, i, False)
        group_id = TgConfig.GROUP_ID
        if group_id:
            try:
                await bot.send_message(chat_id=group_id,
                                       text=f'🎁 Upload\n'
                                            f'🏷️ Item: <b>{item_name}</b>'
                                            f'\n📦 Quantity: <b>{len(values_list)}</b>',
                                       parse_mode='HTML')
            except ChatNotFound:
                pass
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='✅ Item created, product added',
                                    reply_markup=back('item-management'))
        admin_info = await bot.get_chat(user_id)
        logger.info(f"User {user_id} ({admin_info.first_name}) "
                    f'created new item "{item_name}"')
    else:
        if message.photo:
            file_path = get_next_file_path(item_name)

            file_path = get_next_file_path(item_name)

            file_name = f"{item_name}_{int(datetime.datetime.now().timestamp())}.jpg"
            file_path = os.path.join('assets', 'uploads', file_name)
            await message.photo[-1].download(destination_file=file_path)
            value = file_path
        else:
            value = message.text
        await bot.delete_message(chat_id=message.chat.id,
                                 message_id=message.message_id)
        create_item(item_name, item_description, item_price, category_name)
        add_values_to_item(item_name, value, True)
        group_id = TgConfig.GROUP_ID if TgConfig.GROUP_ID != -988765433 else None
        if group_id:
            try:
                await bot.send_message(chat_id=group_id,
                                       text=f'🎁 Upload\n'
                                            f'🏷️ Item: <b>{item_name}</b>'
                                            f'\n📦 Quantity: <b>unlimited</b>',
                                       parse_mode='HTML')
            except ChatNotFound:
                pass
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='✅ Item created, product added',
                                    reply_markup=back('item-management'))
        admin_info = await bot.get_chat(user_id)
        logger.info(f"User {user_id} ({admin_info.first_name}) "
                    f'created new item "{item_name}"')


async def update_item_amount_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[f'{user_id}_message_id'] = call.message.message_id
    TgConfig.STATE[user_id] = 'update_amount_of_item'
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        await bot.edit_message_text('🏷️ Įveskite prekės pavadinimą',
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=back("item-management"))
        return
    await call.answer('Insufficient rights')


async def check_item_name_for_amount_upd(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    item_name = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    item = check_item(item_name)
    if not item:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='❌ Товар не может быть добавлен (Такой позиции не существует)',
                                    reply_markup=back('goods_management'))
    else:
        if check_value(item_name) is False:
            TgConfig.STATE[user_id] = 'add_new_amount'
            TgConfig.STATE[f'{user_id}_name'] = message.text
            await bot.edit_message_text(chat_id=message.chat.id,
                                        message_id=message_id,
                                        text='Enter items for the position separated by ;:',
                                        reply_markup=back('goods_management'))
        else:
            await bot.edit_message_text(chat_id=message.chat.id,
                                        message_id=message_id,
                                        text='❌ Товар не может быть добавлен (У данной позиции бесконечный товар)',
                                        reply_markup=back('goods_management'))


async def updating_item_amount(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    if message.photo:
        file_path = get_next_file_path(TgConfig.STATE.get(f'{user_id}_name'))

        file_path = get_next_file_path(TgConfig.STATE.get(f'{user_id}_name'))

        file_name = f"{TgConfig.STATE.get(f'{user_id}_name')}_{int(datetime.datetime.now().timestamp())}.jpg"
        file_path = os.path.join('assets', 'uploads', file_name)
        await message.photo[-1].download(destination_file=file_path)
        values_list = [file_path]
    else:
        values_list = message.text.split(';')
    TgConfig.STATE[user_id] = None
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    item_name = TgConfig.STATE.get(f'{user_id}_name')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    for i in values_list:
        add_values_to_item(item_name, i, False)
    group_id = TgConfig.GROUP_ID if TgConfig.GROUP_ID != -988765433 else None
    if group_id:
        try:
            await bot.send_message(chat_id=group_id,
                                   text=f'🎁 Upload\n'
                                        f'🏷️ Item: <b>{item_name}</b>'
                                        f'\n📦 Quantity: <b>{len(values_list)}</b>',
                                   parse_mode='HTML')
        except ChatNotFound:
            pass
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='✅ Товар добавлен',
                                reply_markup=back('goods_management'))
    admin_info = await bot.get_chat(user_id)
    logger.info(f"User {user_id} ({admin_info.first_name}) "
                f'добавил товары к позиции "{item_name}" в количестве {len(values_list)} шт')


async def update_item_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = 'check_item_name'
    TgConfig.STATE[f'{user_id}_message_id'] = call.message.message_id
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        await bot.edit_message_text('🏷️ Įveskite prekės pavadinimą',
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=back("goods_management"))
        return
    await call.answer('Insufficient rights')


async def check_item_name_for_update(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    item_name = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    item = check_item(item_name)
    if not item:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='❌ Item cannot be changed (does not exist)',
                                    reply_markup=back('goods_management'))
        return
    TgConfig.STATE[user_id] = 'update_item_name'
    TgConfig.STATE[f'{user_id}_old_name'] = message.text
    TgConfig.STATE[f'{user_id}_category'] = item['category_name']
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='Введите новое имя для позиции:',
                                reply_markup=back('goods_management'))


async def update_item_name(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    TgConfig.STATE[f'{user_id}_name'] = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    TgConfig.STATE[user_id] = 'update_item_description'
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='Enter description for item:',
                                reply_markup=back('goods_management'))


async def update_item_description(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    TgConfig.STATE[f'{user_id}_description'] = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    TgConfig.STATE[user_id] = 'update_item_price'
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='Enter price for item:',
                                reply_markup=back('goods_management'))


async def update_item_price(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    TgConfig.STATE[user_id] = None
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    if not message.text.isdigit():
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='⚠️ Invalid price value.',
                                    reply_markup=back('goods_management'))
        return
    TgConfig.STATE[f'{user_id}_price'] = message.text
    item_old_name = TgConfig.STATE.get(f'{user_id}_old_name')
    if check_value(item_old_name) is False:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='Do you want to make unlimited goods?',
                                    reply_markup=question_buttons('change_make_infinity', 'goods_management'))
    else:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='Do you want to disable unlimited goods?',
                                    reply_markup=question_buttons('change_deny_infinity', 'goods_management'))


async def update_item_process(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    answer = call.data.split('_')
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    item_old_name = TgConfig.STATE.get(f'{user_id}_old_name')
    item_new_name = TgConfig.STATE.get(f'{user_id}_name')
    item_description = TgConfig.STATE.get(f'{user_id}_description')
    category = TgConfig.STATE.get(f'{user_id}_category')
    price = TgConfig.STATE.get(f'{user_id}_price')
    if answer[3] == 'no':
        TgConfig.STATE[user_id] = None
        update_item(item_old_name, item_new_name, item_description, price, category)
        await bot.edit_message_text(chat_id=call.message.chat.id,
                                    message_id=message_id,
                                    text='✅ Item updated',
                                    reply_markup=back('goods_management'))
        admin_info = await bot.get_chat(user_id)
        logger.info(f"User {user_id} ({admin_info.first_name}) "
                    f'обновил позицию "{item_old_name}" на "{item_new_name}"')
    else:
        if answer[1] == 'make':
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=message_id,
                                        text='Enter item value:',
                                        reply_markup=back('goods_management'))
            TgConfig.STATE[f'{user_id}_change'] = 'make'
        elif answer[1] == 'deny':
            await bot.edit_message_text(chat_id=call.message.chat.id,
                                        message_id=message_id,
                                        text='Enter items for the position separated by ;:',
                                        reply_markup=back('goods_management'))
            TgConfig.STATE[f'{user_id}_change'] = 'deny'
    TgConfig.STATE[user_id] = 'apply_change'


async def update_item_infinity(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    if message.photo:
        file_path = get_next_file_path(TgConfig.STATE.get(f'{user_id}_old_name'))

        file_path = get_next_file_path(TgConfig.STATE.get(f'{user_id}_old_name'))

        file_name = f"{TgConfig.STATE.get(f'{user_id}_old_name')}_{int(datetime.datetime.now().timestamp())}.jpg"
        file_path = os.path.join('assets', 'uploads', file_name)

        await message.photo[-1].download(destination_file=file_path)
        msg = file_path
    else:
        msg = message.text
    change = TgConfig.STATE[f'{user_id}_change']
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    item_old_name = TgConfig.STATE.get(f'{user_id}_old_name')
    item_new_name = TgConfig.STATE.get(f'{user_id}_name')
    item_description = TgConfig.STATE.get(f'{user_id}_description')
    category = TgConfig.STATE.get(f'{user_id}_category')
    price = TgConfig.STATE.get(f'{user_id}_price')
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    if change == 'make':
        delete_only_items(item_old_name)
        add_values_to_item(item_old_name, msg, False)
    elif change == 'deny':
        delete_only_items(item_old_name)
        values_list = msg.split(';')
        for i in values_list:
            add_values_to_item(item_old_name, i, False)
    TgConfig.STATE[user_id] = None
    update_item(item_old_name, item_new_name, item_description, price, category)
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='✅ Item updated',
                                reply_markup=back('goods_management'))
    admin_info = await bot.get_chat(user_id)
    logger.info(f"User {user_id} ({admin_info.first_name}) "
                f'обновил позицию "{item_old_name}" на "{item_new_name}"')


async def delete_item_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[f'{user_id}_message_id'] = call.message.message_id
    TgConfig.STATE[user_id] = 'process_removing_item'
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        await bot.edit_message_text('🏷️ Įveskite prekės pavadinimą',
                                    chat_id=call.message.chat.id,
                                    message_id=call.message.message_id,
                                    reply_markup=back("goods_management"))
        return
    await call.answer('Insufficient rights')


async def delete_str_item(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    msg = message.text
    TgConfig.STATE[user_id] = None
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    item = check_item(msg)
    await bot.delete_message(chat_id=message.chat.id,
                             message_id=message.message_id)
    if not item:
        await bot.edit_message_text(chat_id=message.chat.id,
                                    message_id=message_id,
                                    text='❌ Item not deleted (does not exist)',
                                    reply_markup=back('goods_management'))
        return
    delete_item(msg)
    await bot.edit_message_text(chat_id=message.chat.id,
                                message_id=message_id,
                                text='✅ Item deleted',
                                reply_markup=back('goods_management'))
    admin_info = await bot.get_chat(user_id)
    logger.info(f"User {user_id} ({admin_info.first_name}) "
                f'удалил позицию "{msg}"')


async def show_bought_item_callback_handler(call: CallbackQuery):
    bot, user_id = await get_bot_user_ids(call)
    TgConfig.STATE[user_id] = 'show_item'
    TgConfig.STATE[f'{user_id}_message_id'] = call.message.message_id
    role = check_role(user_id)
    if role >= Permission.SHOP_MANAGE:
        await bot.edit_message_text(
            '🔍 Enter the unique ID of the purchased item',
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=back("goods_management"))
        return
    await call.answer('Insufficient rights')


async def process_item_show(message: Message):
    bot, user_id = await get_bot_user_ids(message)
    msg = message.text
    message_id = TgConfig.STATE.get(f'{user_id}_message_id')
    TgConfig.STATE[user_id] = None
    item = select_bought_item(msg)
    await bot.delete_message(chat_id=message.chat.id, message_id=message.message_id)
    if item:
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=message_id,
            text=f'<b>Item</b>: <code>{item["item_name"]}</code>\n'
                 f'<b>Price</b>: <code>{item["price"]}</code>€\n'
                 f'<b>Purchase date</b>: <code>{item["bought_datetime"]}</code>\n'
                 f'<b>Buyer</b>: <code>{item["buyer_id"]}</code>\n'
                 f'<b>Unique operation ID</b>: <code>{item["unique_id"]}</code>\n'
                 f'<b>Value</b>:\n<code>{item["value"]}</code>',
            parse_mode='HTML',
            reply_markup=back('show_bought_item')
        )
        return
    await bot.edit_message_text(
        chat_id=message.chat.id,
        message_id=message_id,
        text='❌ Item with the specified unique ID was not found',
        reply_markup=back('show_bought_item')
    )



def register_shop_management(dp: Dispatcher) -> None:
    dp.register_callback_query_handler(statistics_callback_handler,
                                       lambda c: c.data == 'statistics')
    dp.register_callback_query_handler(goods_settings_menu_callback_handler,
                                       lambda c: c.data == 'item-management')
    dp.register_callback_query_handler(add_item_callback_handler,
                                       lambda c: c.data == 'add_item')
    dp.register_callback_query_handler(update_item_amount_callback_handler,
                                       lambda c: c.data == 'update_item_amount')
    dp.register_callback_query_handler(update_item_callback_handler,
                                       lambda c: c.data == 'update_item')
    dp.register_callback_query_handler(delete_item_callback_handler,
                                       lambda c: c.data == 'delete_item')
    dp.register_callback_query_handler(show_bought_item_callback_handler,
                                       lambda c: c.data == 'show_bought_item')
    dp.register_callback_query_handler(shop_callback_handler,
                                       lambda c: c.data == 'shop_management')
    dp.register_callback_query_handler(logs_callback_handler,
                                       lambda c: c.data == 'show_logs')
    dp.register_callback_query_handler(goods_management_callback_handler,
                                       lambda c: c.data == 'goods_management')
    dp.register_callback_query_handler(categories_callback_handler,
                                       lambda c: c.data == 'categories_management')
    dp.register_callback_query_handler(add_category_callback_handler,
                                       lambda c: c.data == 'add_category')
    dp.register_callback_query_handler(add_subcategory_callback_handler,
                                       lambda c: c.data == 'add_subcategory')
    dp.register_callback_query_handler(delete_category_callback_handler,
                                       lambda c: c.data == 'delete_category')
    dp.register_callback_query_handler(update_category_callback_handler,
                                       lambda c: c.data == 'update_category')

    dp.register_message_handler(check_item_name_for_amount_upd,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'update_amount_of_item')
    dp.register_message_handler(updating_item_amount,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'add_new_amount')
    dp.register_message_handler(check_item_name_for_add,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'create_item_name')
    dp.register_message_handler(add_item_description,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'create_item_description')
    dp.register_message_handler(add_item_price,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'create_item_price')
    dp.register_message_handler(check_category_for_add_item,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'check_item_category')
    dp.register_message_handler(adding_item,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'add_item_value')
    dp.register_message_handler(check_item_name_for_update,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'check_item_name')
    dp.register_message_handler(update_item_name,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'update_item_name')
    dp.register_message_handler(update_item_description,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'update_item_description')
    dp.register_message_handler(update_item_price,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'update_item_price')
    dp.register_message_handler(delete_str_item,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'process_removing_item')
    dp.register_message_handler(process_item_show,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'show_item')
    dp.register_message_handler(process_category_for_add,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'add_category')
    dp.register_message_handler(process_subcategory_parent,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'add_subcategory_parent')
    dp.register_message_handler(process_subcategory_name,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'add_subcategory_name')
    dp.register_message_handler(process_category_for_delete,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'delete_category')
    dp.register_message_handler(check_category_for_update,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'check_category')
    dp.register_message_handler(check_category_name_for_update,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'update_category_name')
    dp.register_message_handler(update_item_infinity,
                                lambda c: TgConfig.STATE.get(c.from_user.id) == 'apply_change')

    dp.register_callback_query_handler(adding_value_to_position,
                                       lambda c: c.data.startswith('infinity_'))
    dp.register_callback_query_handler(update_item_process,
                                       lambda c: c.data.startswith('change_'))
