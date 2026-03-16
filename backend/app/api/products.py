from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.core.database import get_db
from app.models.db_models import Product, ProductPriceHistory
from app.models.schemas import ProductResponse, ProductPriceHistoryResponse
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/products", tags=["products"])


class ProductUpdateRequest(BaseModel):
    """商品更新请求"""
    name: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category: Optional[str] = None


@router.get("", response_model=List[ProductResponse])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """获取商品列表"""
    query = db.query(Product)
    
    if category:
        query = query.filter(Product.category == category)
    
    if search:
        query = query.filter(Product.name.ilike(f"%{search}%"))
    
    products = query.offset(skip).limit(limit).all()
    
    return [
        ProductResponse(
            id=p.id,
            name=p.name,
            sku=p.sku,
            price=p.price,
            stock=p.stock or 0,
            category=p.category or "未分类",
            created_at=p.created_at,
        )
        for p in products
    ]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: Session = Depends(get_db),
):
    """获取商品详情"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    return ProductResponse(
        id=product.id,
        name=product.name,
        sku=product.sku,
        price=product.price,
        stock=product.stock or 0,
        category=product.category or "未分类",
        created_at=product.created_at,
    )


@router.put("/{product_id}")
async def update_product(
    product_id: int,
    request: ProductUpdateRequest,
    db: Session = Depends(get_db),
):
    """更新商品信息（手动修改，记录价格变更）"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    # 如果修改了价格，记录历史
    if request.price is not None and request.price != product.price:
        history = ProductPriceHistory(
            product_id=product.id,
            old_price=product.price,
            new_price=request.price,
            changed_by="user",
            changed_by_id=1,  # TODO: 从token获取当前用户ID
            reason="用户手动修改",
        )
        db.add(history)
        product.price = request.price
    
    # 更新其他字段
    if request.name is not None:
        product.name = request.name
    if request.stock is not None:
        product.stock = request.stock
    if request.category is not None:
        product.category = request.category
    
    db.commit()
    db.refresh(product)
    
    return {
        "status": "success",
        "message": "商品更新成功",
        "product": {
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "stock": product.stock,
        },
    }


@router.get("/{product_id}/price-history", response_model=List[ProductPriceHistoryResponse])
async def get_product_price_history(
    product_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取商品价格修改历史"""
    # 检查商品是否存在
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="商品不存在")
    
    history = db.query(ProductPriceHistory).filter(
        ProductPriceHistory.product_id == product_id
    ).order_by(desc(ProductPriceHistory.created_at)).limit(limit).all()
    
    return [
        ProductPriceHistoryResponse(
            id=h.id,
            product_id=h.product_id,
            product_name=product.name,
            old_price=h.old_price,
            new_price=h.new_price,
            changed_by=h.changed_by,
            changed_by_id=h.changed_by_id,
            reason=h.reason,
            created_at=h.created_at,
        )
        for h in history
    ]


@router.get("/price-history/recent")
async def get_recent_price_changes(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """获取最近的价格修改记录（所有商品）"""
    history = db.query(ProductPriceHistory).order_by(
        desc(ProductPriceHistory.created_at)
    ).limit(limit).all()
    
    result = []
    for h in history:
        product = db.query(Product).filter(Product.id == h.product_id).first()
        result.append({
            "id": h.id,
            "product_id": h.product_id,
            "product_name": product.name if product else "未知商品",
            "old_price": h.old_price,
            "new_price": h.new_price,
            "changed_by": h.changed_by,
            "reason": h.reason,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        })
    
    return {
        "total": len(result),
        "items": result,
    }
