from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Product, Review, Wishlist, User
from app.schemas import ReviewCreate, ReviewOut, ProductOut
from app.auth import get_current_user

router = APIRouter(prefix="/api", tags=["Reviews & Wishlist"])


@router.post("/products/{product_id}/reviews", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def add_or_update_review(
    product_id: int,
    payload: ReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    existing = (
        db.query(Review)
        .filter(Review.user_id == current_user.id, Review.product_id == product_id)
        .first()
    )

    if existing:
        existing.rating = payload.rating
        existing.comment = payload.comment.strip()
        review = existing
    else:
        review = Review(
            user_id=current_user.id,
            product_id=product_id,
            rating=payload.rating,
            comment=payload.comment.strip(),
        )
        db.add(review)

    db.flush()

    # Recalculate product rating_avg and review_count from all reviews
    all_reviews = db.query(Review).filter(Review.product_id == product_id).all()
    product.review_count = len(all_reviews)
    product.rating_avg = (
        round(sum(r.rating for r in all_reviews) / len(all_reviews), 1)
        if all_reviews
        else 0.0
    )

    db.commit()
    db.refresh(review)

    return ReviewOut(
        id=review.id,
        user_id=review.user_id,
        user_name=current_user.name,
        product_id=review.product_id,
        rating=review.rating,
        comment=review.comment,
        created_at=review.created_at,
    )


@router.get("/wishlist", response_model=List[ProductOut])
def get_wishlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    entries = db.query(Wishlist).filter(Wishlist.user_id == current_user.id).all()
    return [e.product for e in entries if e.product]


@router.post("/wishlist/{product_id}")
def toggle_wishlist(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found.")

    existing = (
        db.query(Wishlist)
        .filter(Wishlist.user_id == current_user.id, Wishlist.product_id == product_id)
        .first()
    )
    if existing:
        db.delete(existing)
        db.commit()
        return {"wishlisted": False, "product_id": product_id}

    db.add(Wishlist(user_id=current_user.id, product_id=product_id))
    db.commit()
    return {"wishlisted": True, "product_id": product_id}
