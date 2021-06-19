from SaitamaRobot import mongodb as db_x

Eren = db_x["CHATBOT"]


def add_chat(chat_id):
    stark = Eren.find_one({"chat_id": chat_id})
    if stark:
        return False
    else:
        Eren.insert_one({"chat_id": chat_id})
        return True


def remove_chat(chat_id):
    stark = Eren.find_one({"chat_id": chat_id})
    if not stark:
        return False
    else:
        Eren.delete_one({"chat_id": chat_id})
        return True


def get_all_chats():
    r = list(Eren.find())
    if r:
        return r
    else:
        return False


def get_session(chat_id):
    stark = Eren.find_one({"chat_id": chat_id})
    if not stark:
        return False
    else:
        return stark
