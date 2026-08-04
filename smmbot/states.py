from aiogram.fsm.state import State, StatesGroup

class OrderStates(StatesGroup):
    select_category = State()
    select_service = State()
    get_link = State()
    get_quantity = State()
    confirm = State()

class RefillStates(StatesGroup):
    get_amount = State()
    get_check = State()

class QuestionStates(StatesGroup):
    ask_question = State()

class ContactStates(StatesGroup):
    get_message = State()

class AddCategoryStates(StatesGroup):
    get_name = State()

class AddServiceStates(StatesGroup):
    get_category = State()
    get_name = State()
    get_api_id = State()
    get_price = State()
    get_min = State()
    get_max = State()

class EditServiceStates(StatesGroup):
    choose_field = State()
    get_name = State()
    get_api_id = State()
    get_price = State()

class ContestStates(StatesGroup):
    get_title = State()
    get_description = State()
    get_days = State()

class ContestPrizesStates(StatesGroup):
    get_prize1 = State()
    get_prize2 = State()
    get_prize3 = State()

class BroadcastStates(StatesGroup):
    get_message = State()
    confirm = State()

class CardStates(StatesGroup):
    get_card_number = State()
    get_full_name = State()

class PaymentNoteStates(StatesGroup):
    get_note = State()

class PaymentExtraStates(StatesGroup):
    get_amount = State()

class AnswerQuestionStates(StatesGroup):
    get_answer = State()

class UserBalanceStates(StatesGroup):
    get_amount = State()

class UserMessageStates(StatesGroup):
    get_message = State()