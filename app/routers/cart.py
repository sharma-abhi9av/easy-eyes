from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CartItem, Product, User
from app.schemas import CartItemAdd, CartItemUpdate, CartOut, CartItemOut
from app.auth import get_current_user

router = APIRouter(prefix="/api/cart", tags=["Cart"])


def _build_cart_response(db: Session, user_id: int) -> CartOut:
    items = db.query(CartItem).filter(CartItem.user_id == user_id).all()
    cart_items_out = []
    subtotal = 0
    total_items = 0

    for item in items:
        if not item.product:
            continue
        line_total = item.product.price * item.quantity
        subtotal += line_total
        total_items += item.quantity
        cart_items_out.append(
            CartItemOut(
                id=item.id,
                product_id=item.product_id,
                quantity=item.quantity,
                line_total=line_total,
                product=item.product,
            )
        )

    return CartOut(items=cart_items_out, total_items=total_items, subtotal=subtotal)


@router.get("", response_model=CartOut)
def get_cart(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _build_cart_response(db, current_user.id)


@router.post("", response_model=CartOut, status_code=status.HTTP_201_CREATED)
def add_to_cart(
    payload: CartItemAdd,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == payload.product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    existing_item = (
        db.query(CartItem)
        .filter(CartItem.user_id == current_user.id, CartItem.product_id == payload.product_id)
        .first()
    )

    new_qty = (existing_item.quantity + payload.quantity) if existing_item else payload.quantity
    if new_qty > product.stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {product.stock} unit(s) of '{product.name}' available in stock.",
        )

    if existing_item:
        existing_item.quantity = new_qty
    else:
        db.add(
            CartItem(
                user_id=current_user.id,
                product_id=payload.product_id,
                quantity=payload.quantity,
            )
        )

    db.commit()
    return _build_cart_response(db, current_user.id)


@router.patch("/{item_id}", response_model=CartOut)
def update_cart_item(
    item_id: int,
    payload: CartItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # BOLA defense: filter by both item_id AND current_user.id
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")

    if payload.quantity > item.product.stock:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only {item.product.stock} unit(s) available in stock.",
        )

    item.quantity = payload.quantity
    db.commit()
    return _build_cart_response(db, current_user.id)


@router.delete("/{item_id}", response_model=CartOut)
def remove_cart_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = (
        db.query(CartItem)
        .filter(CartItem.id == item_id, CartItem.user_id == current_user.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found.")

    db.delete(item)
    db.commit()
    return _build_cart_response(db, current_user.id)
