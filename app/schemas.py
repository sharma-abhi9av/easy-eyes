from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict


class UserSignup(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator("password")
    @classmethod
    def check_bcrypt_byte_limit(cls, v: str) -> str:
        if len(v.encode("utf-8")) > 72:
            raise ValueError("Password cannot exceed 72 UTF-8 bytes (bcrypt limit).")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=72)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime


class AuthResponse(BaseModel):
    message: str
    user: UserOut
    access_token: str


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Star rating from 1 to 5")
    comment: str = Field(..., min_length=3, max_length=800)


class ReviewOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    user_name: str
    product_id: int
    rating: int
    comment: str
    created_at: datetime


class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    sku: str = Field(..., min_length=3, max_length=50)
    price: int = Field(..., gt=0, description="Price in INR")
    description: str = Field(..., min_length=10)
    image_url: str = Field(..., min_length=5, max_length=255)
    category: str = Field(..., pattern="^(SUNGLASSES|OPTICAL)$")
    frame_shape: str = Field(..., pattern="^(AVIATOR|ROUND|SQUARE|CAT_EYE|RECTANGLE)$")
    frame_material: str = Field(..., pattern="^(TITANIUM|ACETATE|METAL)$")
    lens_type: str = Field(..., pattern="^(POLARIZED|BLUE_LIGHT|TINTED)$")
    stock: int = Field(..., ge=0)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=150)
    sku: Optional[str] = Field(None, min_length=3, max_length=50)
    price: Optional[int] = Field(None, gt=0)
    description: Optional[str] = Field(None, min_length=10)
    image_url: Optional[str] = None
    category: Optional[str] = Field(None, pattern="^(SUNGLASSES|OPTICAL)$")
    frame_shape: Optional[str] = Field(None, pattern="^(AVIATOR|ROUND|SQUARE|CAT_EYE|RECTANGLE)$")
    frame_material: Optional[str] = Field(None, pattern="^(TITANIUM|ACETATE|METAL)$")
    lens_type: Optional[str] = Field(None, pattern="^(POLARIZED|BLUE_LIGHT|TINTED)$")
    stock: Optional[int] = Field(None, ge=0)


class ProductOut(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    rating_avg: float
    review_count: int


class ProductDetailOut(ProductOut):
    reviews: List[ReviewOut] = []


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(1, ge=1, le=99)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=1, le=99)


class CartItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    quantity: int
    line_total: int
    product: ProductOut


class CartOut(BaseModel):
    items: List[CartItemOut]
    total_items: int
    subtotal: int


class CheckoutRequest(BaseModel):
    shipping_address: str = Field(..., min_length=10, max_length=500)


class CheckoutInitResponse(BaseModel):
    order_id: int
    razorpay_order_id: str
    amount_paise: int
    total_amount_inr: int
    currency: str
    razorpay_key_id: str
    is_simulated: bool
    customer_name: str
    customer_email: str


class PaymentVerifyRequest(BaseModel):
    order_id: int
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class OrderStatusUpdate(BaseModel):
    order_status: str = Field(..., pattern="^(PROCESSING|SHIPPED|DELIVERED|CANCELLED)$")


class OrderItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    product_name_snapshot: str
    price_snapshot: int
    quantity: int


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    total_amount: int
    shipping_address: str
    payment_status: str
    razorpay_order_id: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    order_status: str
    created_at: datetime
    items: List[OrderItemOut] = []
