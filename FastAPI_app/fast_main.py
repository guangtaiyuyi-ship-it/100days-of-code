from fastapi import FastAPI
from pydantic import BaseModel

# リクエストデータの定義
class Item(BaseModel):
    name: str
    description: str = None
    price: float
    tax: float = None

# レスポンスデータの定義
class ItemResponse(BaseModel):
    name: str
    price: float
    total: float

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    return {"item_id": item_id}

@app.post("/items/")
def create_item(item: Item):
    return {"item": item, "total": item.price + (item.tax or 0)}

@app.post("/items/", response_model=ItemResponse)
def create_item(item: Item):
    total = item.price + (item.tax or 0)
    return {"name": item.name, "price": item.price, "total": total}
