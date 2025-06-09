from logging import getLogger
from melodm.database.manager import get_current_db_manager
from pydantic import BaseModel, Field


from bson import ObjectId
from typing import Any, ClassVar, Dict, List, Tuple
from datetime import datetime

from pymongo import IndexModel
from pymongo.asynchronous.cursor import AsyncCursor

logger = getLogger(__file__)


class Query:
  def __init__(self, cursor: AsyncCursor[Any]):
    self.cursor = cursor

  def skip(self, skip: int):
    self.cursor = self.cursor.skip(skip)
    return self

  def limit(self, limit: int):
    self.cursor = self.cursor.limit(limit)
    return self

  async def to_list(self):
    return await self.cursor.to_list()

class PyObjectId(ObjectId):
    @classmethod
    def validate(cls, v: ObjectId):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid objectid")
        return ObjectId(v)

class UpdateDocument(BaseModel):
  pass

class Settings(BaseModel):
  collection_name: str = "sa"
  # update_model: UpdateDocument
  indexed_fields: List[Tuple[str,int]] = [
      ("test", -1),
      ("sa", 1)
  ]

class Document(BaseModel):
    mongo_id: str = Field(..., alias="_id")
    created_at: datetime
    updated_at: datetime
    db_model_settings: ClassVar[Settings] = Settings()


    @classmethod
    async def __create_indexes(cls):
      index_models = [IndexModel([(field, direction)], name=field) for field, direction in cls.db_model_settings.indexed_fields]
      print("indexes", index_models)
      collection = cls.__get_collection_for_current_db_context()
      return await collection.create_indexes(index_models)


    @classmethod
    def __get_collection_for_current_db_context(cls):
      db_manager = get_current_db_manager()
      return db_manager.get_collection(cls.__name__.lower())

    @classmethod
    async def insert(cls, filter: Dict[str, Any]= {}):
      collection = cls.__get_collection_for_current_db_context()

      # index_list = [index async for index in await collection.list_indexes()]
      # return index_list

      return await cls.__create_indexes()
      # await cls.__get_collection_for_current_db_context().insert_one(cls)


    @classmethod
    async def update(cls, filter: Dict[str,Any]):
      return cls.__get_collection_for_current_db_context().update_one()

    @classmethod
    def find(cls, filter: Dict[str,Any]) -> Query:
      return Query(cls.__get_collection_for_current_db_context().find())

    @classmethod
    async def find_one(cls, filter: Dict[str,Any]) -> Any:
      return await cls.__get_collection_for_current_db_context().find_one(filter)
