import threading
from config import Config
import sqlalchemy.exc
from sqlalchemy import create_engine
from sqlalchemy import Column, TEXT, Numeric, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import traceback


DB_URI = Config.DATABASE_URI


def start() -> scoped_session:
    # engine = create_engine(DB_URI, client_encoding="utf8")
    engine = create_engine(DB_URI)
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return scoped_session(sessionmaker(bind=engine, autoflush=False))


BASE = declarative_base()
SESSION = start()

INSERTION_LOCK = threading.RLock()


class Pastes(BASE):
    __tablename__ = "pastes"
    pasteID = Column(TEXT, primary_key=True)
    controlid = Column(TEXT)
    content = Column(TEXT)

    def __init__(self, pasteID, controlID, content):
        self.pasteID = pasteID
        self.controlid = controlID
        self.content = content


Pastes.__table__.create(checkfirst=True)


def create_paste(pasteID, controlID, content):
    try:
        with INSERTION_LOCK:
            paste = SESSION.query(Pastes).get(pasteID)
            if paste:
                return {
                    "success": False,
                    "controlID": None,
                    "pasteID": pasteID,
                    "error": "exists",
                }
            paste = Pastes(pasteID, controlID, content)
            SESSION.add(paste)
            SESSION.commit()
            return {
                "success": True,
                "controlID": controlID,
                "pasteID": pasteID,
                "error": "None",
            }
    except sqlalchemy.exc.OperationalError:
        create_paste(pasteID, controlID, content)
    except:
        return {
            "success": False,
            "controlID": controlID,
            "pasteID": pasteID,
            "error": traceback.format_exc(),
        }
    finally:
        SESSION.close()


def edit_paste(pasteID, controlID, content):
    try:
        with INSERTION_LOCK:
            paste = SESSION.query(Pastes).get(pasteID)
            if paste.controlid != controlID:
                return {
                    "success": False,
                    "controlID": controlID,
                    "pasteID": pasteID,
                    "error": "wrong",
                }
            paste.content = content
            SESSION.commit()
            return {
                "success": True,
                "controlID": controlID,
                "pasteID": pasteID,
                "error": "None",
            }
    except sqlalchemy.exc.OperationalError:
        return edit_paste(pasteID, controlID, content)
    except:
        print(traceback.format_exc())
        return {
            "success": False,
            "controlID": controlID,
            "pasteID": pasteID,
            "error": traceback.format_exc(),
        }
    finally:
        SESSION.close()


def get_paste(pasteID):
    try:
        with INSERTION_LOCK:
            paste = SESSION.query(Pastes).get(pasteID)
            if not paste:
                return None
            return paste.content
    except sqlalchemy.exc.OperationalError:
        return get_paste(pasteID)
    finally:
        SESSION.close()


print("DATABASE CONNECTED!")
