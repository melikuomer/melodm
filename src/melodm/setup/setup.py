from typing import List
import asyncio

from ..database.manager import DBContext
from ..types.document import Document


async def initialize_indexes(db_name: str, documents:List[Document]):
  async with DBContext(db_name=db_name):
    await asyncio.gather(*[document.create_indexes() for document in documents])
