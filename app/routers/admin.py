from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Order, User, CartItem, Wishlist
from app.schemas import ProductCreate, ProductUpdate, ProductOut, OrderOut, OrderStatusUpdate
from app.auth import require_admin

router = APIRouter(prefix="/api/admin", tags=["Admin Panel"])


@router.post("/products", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def admin_create_product(
    payload: ProductCreate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    sku_clean = payload.sku.strip().upper()
    existing = db.query(Product).filter(Product.sku == sku_clean).first()
    if existing:
        if not existing.is_active:
            # Reactivate previously soft-deleted SKU with updated attributes
            for field, val in payload.model_dump().items():
                setattr(existing, field, val)
            existing.sku = sku_clean
            existing.is_active = True
            db.commit()
            db.refresh(existing)
            return existing
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A product with SKU '{sku_clean}' already exists.",
        )

    product = Product(
        name=payload.name.strip(),
        sku=sku_clean,
        price=payload.price,
        description=payload.description.strip(),
        image_url=payload.image_url.strip(),
        category=payload.category,
        frame_shape=payload.frame_shape,
        frame_material=payload.frame_material,
        lens_type=payload.lens_type,
        stock=payload.stock,
        rating_avg=0.0,
        review_count=0,
        is_active=True,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.put("/products/{product_id}", response_model=ProductOut)
def admin_update_product(
    product_id: int,
    payload: ProductUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active.is_(True))
        .first()
    )
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    update_data = payload.model_dump(exclude_unset=True, exclude_none=True)
    if "sku" in update_data:
        update_data["sku"] = update_data["sku"].strip().upper()
        clash = (
            db.query(Product)
            .filter(Product.sku == update_data["sku"], Product.id != product_id)
            .first()
        )
        if clash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"SKU '{update_data['sku']}' is already used by another frame.",
            )

    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}")
def admin_delete_product(
    product_id: int,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    product = (
        db.query(Product)
        .filter(Product.id == product_id, Product.is_active.is_(True))
        .first()
    )
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    # Soft delete so past OrderItem foreign keys never break in PostgreSQL
    product.is_active = False
    db.query(CartItem).filter(CartItem.product_id == product.id).delete()
    db.query(Wishlist).filter(Wishlist.product_id == product.id).delete()
    db.commit()
    return {"message": f"Product '{product.name}' removed from the catalogue."}


@router.get("/orders", response_model=List[OrderOut])
def admin_list_all_orders(
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    orders = (
        db.query(Order)
        .filter(Order.payment_status == "PAID")
        .order_by(Order.created_at.desc())
        .all()
    )
    results = []
    for o in orders:
        out = OrderOut.model_validate(o)
        out.customer_name = o.user.name if o.user else "Customer"
        out.customer_email = o.user.email if o.user else ""
        results.append(out)
    return results


@router.patch("/orders/{order_id}/status", response_model=OrderOut)
def admin_update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    _admin: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    order.order_status = payload.order_status
    db.commit()
    db.refresh(order)
    out = OrderOut.model_validate(order)
    out.customer_name = order.user.name if order.user else "Customer"
    out.customer_email = order.user.email if order.user else ""
    return out
