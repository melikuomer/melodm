This project explores a multi-tenant ODM (Object-Document Mapper) approach in Python.

Existing solutions often lack specific mechanisms to guarantee race condition prevention in asynchronous environments with numerous tenants. Furthermore, their reliance on mandatory initializers can limit flexibility.

Therefore, I present **MelODM**:

Specifically designed for multi-tenant architectures with FastAPI in mind. It leverages the modern `AsyncMongoClient` instead of the deprecated `motor` library.

## Basic Usage Example

```python
from melodm.types import Document
from melodm.database import DBContext

class MyDocument(Document):
    my_val: str

async with DBContext("My_Fancy_DB_Name"):
    doc = await MyDocument.find_one({"_id":"12341245154"})

    doc.my_val = "my new value"

    await doc.save()
```

## FastAPI Integration

```python
from fastapi import FastAPI, Depends
from .somewhere_else import main_route
import logging

logger = logging.getLogger(__name__)


async def inject_db():
  async with DBContext("test-app") as ctx:
    logger.info(f"Entered the context for {ctx.db}")
    yield # here This call passes execution with current db context to the route
    logger.info(f"Exited context for {ctx.db}")

app = FastAPI()
app.include_router(main_route, dependencies=[Depends(inject_db)])
```


# Running Tests

```bash
uv run --env-file .env -m tests.test
```
