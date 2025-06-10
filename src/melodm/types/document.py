from typing_extensions import Annotated
from ..database.manager import get_current_db_manager
from pydantic import BaseModel, ConfigDict, Field


from typing import Any, ClassVar, Dict, List, Optional, Unpack
from datetime import datetime

from pymongo import IndexModel
from pymongo.asynchronous.cursor import AsyncCursor


from .object_id import PyObjectId
from .configuration import IndexMetadata, Settings

import logging
logger = logging.getLogger(__name__)


class Query:
  def __init__(self, cursor: AsyncCursor[Any]):
    self.cursor = cursor

  def skip(self, skip: int):
    self.cursor = self.cursor.skip(skip)
    return self

  def limit(self, limit: int):
    self.cursor = self.cursor.limit(limit)
    return self

  def sort(self, sortQuery: Dict[str,Any]):
    self.cursor = self.cursor.sort(sortQuery)
    return self

  async def to_list(self):
    return await self.cursor.to_list()


class Document(BaseModel):
    # --- INSTANCE DATA/STATE ---
    mongo_id: Annotated[Optional[PyObjectId],Field(default=None, alias="_id"),IndexMetadata(unique=True)]
    created_at: datetime
    updated_at: datetime

    _update_list: Dict[str,Any] = {} # Instance-specific change tracking

    # --- CLASS LEVEL METADATA/SETUP ---
    db_model_settings: ClassVar[Settings] = Settings()
    _managed_indexes: ClassVar[List[IndexModel]] = []

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs: Unpack[ConfigDict]):
      super().__pydantic_init_subclass__(**kwargs)
      # logger.info(str(__bases__)
      current_class_indexes: List[IndexModel] = []
      if hasattr(cls, 'model_fields'): # this parts checks if pydantic version is v2
        for field_name, model_field in cls.model_fields.items():
          # now these fields will contain items from annotated
          for meta_item in getattr(model_field, 'metadata', []):
            if isinstance(meta_item, IndexMetadata):
              index_name = meta_item.name or f"{cls.__name__.lower()}_{field_name}_idx"
              current_class_indexes.append(
                IndexModel(
                  [(field_name, meta_item.direction)],
                  name= index_name,
                  unique= meta_item.unique
                )
              )
              break
      logger.info(f'Created indexes: ", {str(current_class_indexes)}')
      cls._managed_indexes = current_class_indexes

    def __setattr__(self, name: str, value: Any, /) -> None:
      logging.info(f"called {name}")

      super().__setattr__(name, value)
      if self.mongo_id is not None and name in type(self).model_fields and name != "_update_list":
        #TODO maybe check if value actually changed?
        self._update_list[name] = value

    # @model_validator(mode='after')
    # def _reset_update_list_on_load(self) -> 'Document':

    #     # After loading from DB (mongo_id is set), clear the update list
    #     # so setting initial values doesn't mark them for update.
    #     if self.mongo_id is not None:
    #         self._update_list = {}
    #     return self

    # --- INSTANCE DATABASE OPERATIONS ---

    async def insert(self):
      doc_data = self.model_dump(by_alias=True, exclude_none=True)
      return await self.__get_collection_for_current_db_context().insert_one(doc_data)

    async def save(self):
      # This instance method saves the current state of the document instance to the database
      if self.mongo_id is None:
          raise ValueError("Cannot save document without an _id. Insert it first.")

      if not self._update_list:
          logger.warning(f"Save called but no changes to save for document {self.mongo_id}")
          return None # Nothing to update
      result = await self.__get_collection_for_current_db_context().update_one({"_id": self.mongo_id}, {"$set": self._update_list})
      if result.modified_count > 0 or result.matched_count > 0:
          self._update_list = {}
          return result
      return None # Or raise an error if update failed

    # --- COLLECTION DATABASE OPERATIONS (Class Methods) ---
    @classmethod
    async def create_indexes(cls):
      """Ensure indexes for this Document class are created in the database.

      This method should typically be called once during application startup.
      Indexes are automatically collected from fields annotated with `IndexMetadata`.

      Returns:
          List[str] | None: A list of index names created, or `None` if no indexes
                            are defined for this class via `IndexMetadata`.
      """
      if not cls._managed_indexes:
        # logger.info(f"No pre-collected indexes defined for {cls.__name__} via IndexMetadata.")
        return None # Or raise an error, or handle as appropriate

      collection = cls.__get_collection_for_current_db_context()
      return await collection.create_indexes(cls._managed_indexes)

    @classmethod
    def __get_collection_for_current_db_context(cls):
      db_manager = get_current_db_manager()
      return db_manager.get_collection(cls.__name__.lower())

    @classmethod
    async def update_many(cls, filter: Dict[str,Any], updateObj: Any):
      return await cls.__get_collection_for_current_db_context().update_many(filter, {"$set":updateObj})

    @classmethod
    def find(cls, filter: Dict[str,Any]) -> Query:
      return Query(cls.__get_collection_for_current_db_context().find(filter))

    @classmethod
    async def find_one(cls, filter: Dict[str,Any]):
      """
      _id automatically converted to ObjectID.
      Remaining conversions should be done manually
      """
      mongo_id = filter.get("_id", None)
      if mongo_id is not None and isinstance(mongo_id, str):
        filter["_id"] = PyObjectId.validate(mongo_id)
      logging.info(filter)
      doc_data = await cls.__get_collection_for_current_db_context().find_one(filter)
      if doc_data is None:
        return None
      return cls.model_validate(doc_data)
