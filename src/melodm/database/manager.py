from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase


from contextvars import ContextVar, Token
from typing import Optional, Any

import logging
logger = logging.getLogger(__name__)

_current_db_manager:ContextVar[Optional['DBContext']] = ContextVar('_current_db_manager', default=None)
class DBManager():
  _instance = None

  def __new__(cls):
    if cls._instance is None:
      cls._instance = super(DBManager, cls).__new__(cls)
      import os
      db_string = os.environ.get("DB_STRING")
      print(f"db string is {db_string}")
      cls._client: AsyncMongoClient[Any] = AsyncMongoClient(db_string)
    return cls._instance

  @classmethod
  def get_db(cls, db_name: str):
    return cls._client.get_database(db_name)

class DBContext():
    def __init__(self, db_name: str):
        manager= DBManager()
        self.db: AsyncDatabase[Any] = manager.get_db(db_name=db_name)
        self.prev_token: Token[Optional['DBContext']]

    def get_collection(self, collection_name: str):
        return self.db.get_collection(collection_name)

    async def __aenter__(self):
        self.prev_token = _current_db_manager.set(self)
        return self

    async def __aexit__(self, exc_type: type[Exception], exc_val: Exception, exc_tb: type[Exception]):
        _current_db_manager.reset(self.prev_token)
        logger.info(f"exited async with: {exc_val}, {exc_tb}")
        #_db_connection.reset()

def get_current_db_manager() -> 'DBContext':
    """
    Retrieves the current TenantDBManager from the context variable for the current task.
    Raises RuntimeError if no manager is set in the context.
    """
    db_manager = _current_db_manager.get()
    if db_manager is None:
        raise RuntimeError("No TenantDBManager found in the current context. Ensure you are using an async context manager (async with TenantDBManager(...):) or a dependency injection framework that sets the context for the current task.")
    # Optionally, add a check here to ensure the manager is 'active' if that state were tracked
    return db_manager
