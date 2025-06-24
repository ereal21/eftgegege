import sqlalchemy.exc
import random
from bot.database.models import User, ItemValues, Goods, Categories, BoughtGoods, \
    Operations, UnfinishedOperations
from bot.database import Database


def create_user(telegram_id: int, registration_date, referral_id, role: int = 1) -> None:
    session = Database().session
    try:
        session.query(User.telegram_id).filter(User.telegram_id == telegram_id).one()
    except sqlalchemy.exc.NoResultFound:
        if referral_id != '':
            session.add(
                User(telegram_id=telegram_id, role_id=role, registration_date=registration_date,
                     referral_id=referral_id))
            session.commit()
        else:
            session.add(
                User(telegram_id=telegram_id, role_id=role, registration_date=registration_date,
                     referral_id=None))
            session.commit()


def create_item(item_name: str, item_description: str, item_price: int, category_name: str) -> None:
    session = Database().session
    session.add(
        Goods(name=item_name, description=item_description, price=item_price, category_name=category_name))
    session.commit()


def add_values_to_item(item_name: str, value: str, is_infinity: bool) -> None:
    session = Database().session
    if is_infinity is False:
        session.add(
            ItemValues(name=item_name, value=value, is_infinity=False))
    else:
        session.add(
            ItemValues(name=item_name, value=value, is_infinity=True))
    session.commit()


def create_category(category_name: str, parent: str | None = None) -> None:
    session = Database().session
    session.add(
        Categories(name=category_name, parent_name=parent))
    session.commit()


def create_operation(user_id: int, value: int, operation_time: str) -> None:
    session = Database().session
    session.add(
        Operations(user_id=user_id, operation_value=value, operation_time=operation_time))
    session.commit()


def start_operation(user_id: int, value: int, operation_id: str) -> None:
    session = Database().session
    session.add(
        UnfinishedOperations(user_id=user_id, operation_value=value, operation_id=operation_id))
    session.commit()


def add_bought_item(item_name: str, value: str, price: int, buyer_id: int,
                    bought_time: str) -> None:
    session = Database().session
    session.add(
        BoughtGoods(name=item_name, value=value, price=price, buyer_id=buyer_id, bought_datetime=bought_time,
                    unique_id=str(random.randint(1000000000, 9999999999))))
    session.commit()
