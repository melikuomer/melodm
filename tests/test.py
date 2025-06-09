import asyncio
from melodm.database.manager import DBContext
from melodm.types.document import Document, Settings
from pymongo import AsyncMongoClient

class Auth(Document):
    name: str

    db_model_settings= Settings(
      collection_name= "test",
      indexed_fields= [
          ("valla", -1),
          ("mi", 1)
      ]
    )

async def test():

    async with DBContext("test") as db_context:
      from datetime import datetime
      auth = Auth(
        _id="test_auth",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        name="Test"
      )


      val = await auth.insert()
      print(val)






if __name__ == "__main__":
    asyncio.run(test())
