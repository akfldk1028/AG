"""
FastAPI CRUD API 예제
- Item 리소스에 대한 Create, Read, Update, Delete 기능 제공
- In-memory 저장소 사용 (실제 환경에서는 DB로 대체)
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import uuid4

app = FastAPI(
    title="FastAPI CRUD Example",
    description="Item 리소스에 대한 CRUD API",
    version="1.0.0"
)

# ============ Models ============

class ItemCreate(BaseModel):
    """Item 생성 요청"""
    name: str = Field(..., min_length=1, max_length=100, description="아이템 이름")
    description: Optional[str] = Field(None, max_length=500, description="설명")
    price: float = Field(..., gt=0, description="가격 (0보다 커야 함)")
    quantity: int = Field(default=0, ge=0, description="수량")


class ItemUpdate(BaseModel):
    """Item 수정 요청 (모든 필드 선택적)"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)


class Item(BaseModel):
    """Item 응답"""
    id: str
    name: str
    description: Optional[str]
    price: float
    quantity: int
    created_at: datetime
    updated_at: datetime


# ============ In-Memory Storage ============

items_db: dict[str, Item] = {}


# ============ API Endpoints ============

@app.get("/")
async def root():
    """API 상태 확인"""
    return {"message": "FastAPI CRUD API", "status": "running"}


@app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
async def create_item(item: ItemCreate):
    """새 Item 생성"""
    item_id = str(uuid4())
    now = datetime.now()

    new_item = Item(
        id=item_id,
        name=item.name,
        description=item.description,
        price=item.price,
        quantity=item.quantity,
        created_at=now,
        updated_at=now
    )

    items_db[item_id] = new_item
    return new_item


@app.get("/items", response_model=list[Item])
async def list_items(skip: int = 0, limit: int = 10):
    """모든 Item 조회 (페이지네이션)"""
    items = list(items_db.values())
    return items[skip : skip + limit]


@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str):
    """특정 Item 조회"""
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id '{item_id}' not found"
        )
    return items_db[item_id]


@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: str, item: ItemUpdate):
    """Item 수정 (부분 업데이트)"""
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id '{item_id}' not found"
        )

    stored_item = items_db[item_id]
    update_data = item.model_dump(exclude_unset=True)

    updated_item = stored_item.model_copy(
        update={
            **update_data,
            "updated_at": datetime.now()
        }
    )

    items_db[item_id] = updated_item
    return updated_item


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(item_id: str):
    """Item 삭제"""
    if item_id not in items_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Item with id '{item_id}' not found"
        )

    del items_db[item_id]
    return None


# ============ Run Server ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
