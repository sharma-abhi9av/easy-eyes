import os
import hmac
import hashlib
import uuid
from typing import List
import requests
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from app.database import get_db
from app.models import Order, OrderItem, CartItem, Product, User
from app.schemas import CheckoutRequest, CheckoutInitResponse, PaymentVerifyRequest, OrderOut
from app.auth import get_current_user

load_dotenv()

router = APIRouter(prefix="/api/orders", tags=["Orders"])

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "rzp_test_placeholder")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "secret_placeholder")


def _is_real_razorpay_configured() -> bool:
    return (
        RAZORPAY_KEY_ID.startswith("rzp_test_")
        and RAZORPAY_KEY_ID != "rzp_test_placeholder"
        and RAZORPAY_KEY_SECRET != "secret_placeholder"
    )


@router.post("/checkout", response_model=CheckoutInitResponse, status_code=status.HTTP_201_CREATED)
def initiate_checkout(
    payload: CheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cart_items = db.query(CartItem).filter(CartItem.user_id == current_user.id).all()
    if not cart_items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Your cart is empty.",
        )

    total_amount = 0
    order_items_to_create = []

    for c_item in cart_items:
        product = (
            db.query(Product)
            .filter(Product.id == c_item.product_id, Product.is_active.is_(True))
            .first()
        )
        if not product or product.stock < c_item.quantity:
            avail = product.stock if product else 0
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for '{product.name if product else 'Item'}' (Available: {avail}).",
            )
        total_amount += product.price * c_item.quantity
        order_items_to_create.append(
            OrderItem(
                product_id=product.id,
                product_name_snapshot=product.name,
                price_snapshot=product.price,
                quantity=c_item.quantity,
            )
        )

    amount_paise = total_amount * 100
    is_simulated = True
    rzp_order_id = f"order_sim_{uuid.uuid4().hex[:12]}"

    if _is_real_razorpay_configured():
        try:
            resp = requests.post(
                "https://api.razorpay.com/v1/orders",
                auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET),
                json={"amount": amount_paise, "currency": "INR"},
                timeout=10,
            )
            resp.raise_for_status()
            rzp_order_id = resp.json()["id"]
            is_simulated = False
        except requests.RequestException:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Payment gateway unreachable. Please check your Razorpay test keys or try again.",
            )

    order = Order(
        user_id=current_user.id,
        total_amount=total_amount,
        shipping_address=payload.shipping_address.strip(),
        payment_status="PENDING",
        razorpay_order_id=rzp_order_id,
        order_status="PROCESSING",
        items=order_items_to_create,
    )
    db.add(order)
    db.commit()
    db.refresh(order)

    return CheckoutInitResponse(
        order_id=order.id,
        razorpay_order_id=rzp_order_id,
        amount_paise=amount_paise,
        total_amount_inr=total_amount,
        currency="INR",
        razorpay_key_id=RAZORPAY_KEY_ID,
        is_simulated=is_simulated,
        customer_name=current_user.name,
        customer_email=current_user.email,
    )


@router.post("/verify", response_model=OrderOut)
def verify_payment_and_finalize_order(
    payload: PaymentVerifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = (
        db.query(Order)
        .filter(Order.id == payload.order_id, Order.user_id == current_user.id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    if order.payment_status == "PAID":
        return order

    if order.razorpay_order_id != payload.razorpay_order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order ID mismatch.")

    if not order.razorpay_order_id.startswith("order_sim_"):
        msg = f"{payload.razorpay_order_id}|{payload.razorpay_payment_id}".encode("utf-8")
        expected_sig = hmac.new(
            RAZORPAY_KEY_SECRET.encode("utf-8"), msg, hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, payload.razorpay_signature):
            order.payment_status = "FAILED"
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment signature verification failed.",
            )

    for item in order.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product or product.stock < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Stock exhausted for {item.product_name_snapshot}.",
            )
        product.stock -= item.quantity

    order.payment_status = "PAID"
    order.razorpay_payment_id = payload.razorpay_payment_id

    db.query(CartItem).filter(CartItem.user_id == current_user.id).delete()
    db.commit()
    db.refresh(order)

    return order


@router.get("/my", response_model=List[OrderOut])
def get_my_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(Order)
        .filter(Order.user_id == current_user.id, Order.payment_status == "PAID")
        .order_by(Order.created_at.desc())
        .all()
    )
