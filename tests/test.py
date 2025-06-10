import asyncio
from typing import Annotated
from melodm.database.manager import DBContext
from melodm.types.document import Document, Settings, IndexMetadata, Field


import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
class Auth(Document):
    name: str
    val: Annotated[str,Field(),IndexMetadata(unique=True) ]
    db_model_settings= Settings(
      collection_name= "test",
    )

async def test():

    async with DBContext("test") as db_context:
      await Document.create_indexes()
      from datetime import datetime
      auth = await Auth.find_one({"_id": "68481be5444ebcdc37c48a1a"})
      if auth is None:
        print("none found")
      else:
        auth.val = "32"
        auth.val = "32"
        auth.val = "32"
        auth.val = "32"
        val = await auth.save()






if __name__ == "__main__":
    asyncio.run(test())
