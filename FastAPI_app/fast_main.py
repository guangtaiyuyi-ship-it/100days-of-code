from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel

# リクエストデータの定義
class Item(BaseModel):
    name: str
    description: str| None = None
    price: float
    tax: float | None = None

# レスポンスデータの定義
class ItemResponse(BaseModel):
    name: str
    price: float
    total: float

app = FastAPI()

items = {1: "りんご", 2: "みかん", 3: "バナナ"}

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id, "name": items[item_id]}

@app.get("/items/")
def read_items(skip: int = 0, limit: int = 10):
    return {"skip": skip, "limit": limit}

@app.get("/search/")
def search_items(
    q: str | None = Query(default=None, max_length=50, description="検索キーワード"),
    count: int = Query(default=10, ge=1, le=100, description="取得件数"),
):
    return {"query": q, "count": count}

@app.post("/items/")
def create_item(item: Item):
    return {"item": item, "total": item.price + (item.tax or 0)}

@app.post("/items/", response_model=ItemResponse)
def create_item(item: Item):
    total = item.price + (item.tax or 0)
    return {"name": item.name, "price": item.price, "total": total}

@app.post("/items/")
def create_item(item: Item):
    total = item.price + (item.tax or 0)
    return {"message": "作成しました", "item": item, "total": total}
