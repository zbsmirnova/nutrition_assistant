"""An explicit synthetic end-to-end worker exercise. No provider or real sends."""

from uuid import UUID
import sqlalchemy as sa

from nutrition_contracts.common import NutrientValue, NutritionSnapshot

from . import schema as db
from .conversation import ConversationWorker
from .demo import Seed, message, seed_user
from .interpretation import SyntheticParser
from .outbox import OutboxWorker
from .service import FoodService
from .telegram import TelegramIngress, TelegramSender


USER_ID = UUID("a85b9165-2268-41f1-b27a-6239b45116e3")
PRODUCT_NAME = "творог 5% «Марка А»"
TEXT = "Съела 100 г творога 5% «Марка А»"


def dairy_nutrition():
    return NutritionSnapshot(**{key: NutrientValue(value=value, lower=None, upper=None) for key, value in
        {"kcal": "120", "protein_g": "16", "fat_g": "5", "carbs_g": "3"}.items()})


def fixture(text=TEXT, *, amount="100", candidate="c1", date_hint=None):
    return {"source_text": text, "candidate_names": [PRODUCT_NAME], "output": {"schema_version": "1.0", "actions": [{
        "kind": "add_food", "action_id": "a1", "evidence": text, "depends_on": [], "unresolved": [],
        "food": {"kind": "candidate", "candidate_kind": "product", "candidate_ref": candidate},
        "quantity": {"amount": amount, "unit": "g"}, "weight_basis": "as_sold", "date_hint": {"text": date_hint},
        "meal": "unspecified"}]}}


def run_conversation_demo(engine):
    with engine.connect() as connection:
        exists = connection.execute(sa.select(db.users.c.id).where(db.users.c.id == USER_ID)).scalar_one_or_none()
    if exists is None:
        seed = seed_user(engine, user_id=USER_ID, name=PRODUCT_NAME, food_kind="dairy",
                         declared_fat_percent="5", nutrition=dairy_nutrition())
        with engine.begin() as connection:
            connection.execute(db.telegram_accounts.update().where(db.telegram_accounts.c.user_id == USER_ID)
                               .values(bot_id=303))
    else:
        with engine.connect() as connection:
            account = connection.execute(sa.select(db.telegram_accounts).where(
                db.telegram_accounts.c.user_id == USER_ID)).mappings().one()
            product = connection.execute(sa.select(db.product_versions).where(
                db.product_versions.c.user_id == USER_ID)).mappings().one()
            seed = Seed(USER_ID, account["id"], account["telegram_user_id"], product["product_id"],
                        product["id"], product["data_source_id"])
    msg = message(seed, 3001, text=TEXT)
    source = TelegramIngress(engine, 303).accept({"update_id": msg.telegram_update_id, "message": {
        "message_id": msg.telegram_message_id, "date": int(msg.sent_at.timestamp()), "text": TEXT,
        "from": {"id": seed.telegram_user_id, "is_bot": False},
        "chat": {"id": seed.telegram_user_id, "type": "private"}}})
    worker = ConversationWorker(engine)
    first = worker.run_one(USER_ID, SyntheticParser(fixture()), origin=source)
    replay = worker.run_one(USER_ID, SyntheticParser(fixture()), origin=source)
    replies = []

    class SyntheticTelegram:
        bot_id = 303

        def call(self, method, payload, *, timeout=15):
            assert method == "sendMessage"
            replies.append(payload["text"])
            return {"message_id": 93001, "chat": {"id": payload["chat_id"]}}

    delivery = OutboxWorker(engine, bot_id=303).dispatch_one(TelegramSender(SyntheticTelegram()))
    return {"synthetic_demo": True, "worker_status": first["status"], "replay_status": replay["status"],
            "current_day": FoodService(engine).get_day(USER_ID, msg.sent_at.date()).model_dump(mode="json"),
            "delivery": delivery, "rendered_replies": replies}
