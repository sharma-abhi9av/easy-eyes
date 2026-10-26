from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product
from app.schemas import ProductOut, ProductDetailOut, ReviewOut

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=List[ProductOut])
def list_products(
    search: Optional[str] = Query(None, description="Search by frame name, SKU, or description"),
    category: Optional[str] = Query(None, description="SUNGLASSES or OPTICAL"),
    frame_shape: Optional[str] = Query(None, description="AVIATOR, ROUND, SQUARE, CAT_EYE, RECTANGLE"),
    frame_material: Optional[str] = Query(None, description="TITANIUM, ACETATE, METAL"),
    lens_type: Optional[str] = Query(None, description="POLARIZED, BLUE_LIGHT, TINTED"),
    min_price: Optional[int] = Query(None, ge=0),
    max_price: Optional[int] = Query(None, ge=0),
    sort: Optional[str] = Query("featured", description="featured, price_asc, price_desc, rating_desc"),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.is_active.is_(True))

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Product.name.ilike(term),
                Product.description.ilike(term),
                Product.sku.ilike(term),
            )
        )

    if category:
        query = query.filter(Product.category == category.upper())
    if frame_shape:
        query = query.filter(Product.frame_shape == frame_shape.upper())
    if frame_material:
        query = query.filter(Product.frame_material == frame_material.upper())
    if lens_type:
        query = query.filter(Product.lens_type == lens_type.upper())
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "rating_desc":
        query = query.order_by(Product.rating_avg.desc(), Product.review_count.desc())
    else:
        query = query.order_by(Product.id.asc())

    return query.all()


@router.get("/{product_id}", response_model=ProductDetailOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active.is_(True))
        .first()
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Eyewear frame not found.",
        )

    reviews_out = [
        ReviewOut(
            id=r.id,
            user_id=r.user_id,
            user_name=r.user.name if r.user else "Customer",
            product_id=r.product_id,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at,
        )
        for r in sorted(product.reviews, key=lambda x: x.created_at, reverse=True)
    ]

    return ProductDetailOut(
        id=product.id,
        name=product.name,
        sku=product.sku,
        price=product.price,
        description=product.description,
        image_url=product.image_url,
        category=product.category,
        frame_shape=product.frame_shape,
        frame_material=product.frame_material,
        lens_type=product.lens_type,
        stock=product.stock,
        rating_avg=product.rating_avg,
        review_count=product.review_count,
        reviews=reviews_out,
    )
