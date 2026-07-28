from fastapi import FastAPI, HTTPException, Query, Depends
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.orm import Session
from database import engine, Base, get_db

app = FastAPI()

class ItemModel(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    price = Column(Float)
    tax = Column(Float, nullable=True)

Base.metadata.create_all(bind=engine)

class ItemCreate(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None

class ItemResponse(BaseModel):
    name: str
    price: float
    total: float

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/items/{item_id}")
def read_item(item_id: int):
    items = {1: "りんご", 2: "みかん", 3: "バナナ"}
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"item_id": item_id, "name": items[item_id]}


@app.get("/items/")
def get_items(db: Session = Depends(get_db)):
    # データベースからすべてのアイテムを取得
    items = db.query(ItemModel).all()
    return items

@app.get("/search/")
def search_items(
    q: str | None = Query(default=None, max_length=50, description="検索キーワード"),
    count: int = Query(default=10, ge=1, le=100, description="取得件数"),
):
    return {"query": q, "count": count}


@app.post("/items/")
def create_item(item: ItemCreate, db: Session = Depends(get_db)):
    # 1. PydanticモデルからSQLAlchemyのモデル（DB用データ）に変換
    db_item = ItemModel(
        name=item.name, description=item.description, price=item.price, tax=item.tax
    )

    # 2. データベースに保存
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    return {"message": "作成しました", "item": db_item}
