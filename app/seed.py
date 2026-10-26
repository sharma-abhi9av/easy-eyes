import os
from sqlalchemy.orm import Session
from app.models import User, Product, Review
from app.auth import hash_password


INITIAL_PRODUCTS = [
    {
        "name": "The Kyoto Wire — Matte Titanium",
        "sku": "EE-KYO-001",
        "price": 16500,
        "description": "Hand-finished in Sabae using ultra-lightweight beta-titanium. Features filigree temple engraving and anti-reflective polarized lenses.",
        "image_url": "/static/images/frames/frame-1.webp",
        "category": "SUNGLASSES",
        "frame_shape": "ROUND",
        "frame_material": "TITANIUM",
        "lens_type": "POLARIZED",
        "stock": 14,
    },
    {
        "name": "Milan Atelier — Havana Tortoise",
        "sku": "EE-MIL-002",
        "price": 14200,
        "description": "Sculpted from 8mm Italian Mazzucchelli cellulose acetate with custom five-barrel riveted hinges and warm amber CR-39 sun lenses.",
        "image_url": "/static/images/frames/frame-2.webp",
        "category": "SUNGLASSES",
        "frame_shape": "SQUARE",
        "frame_material": "ACETATE",
        "lens_type": "TINTED",
        "stock": 18,
    },
    {
        "name": "Aether Navigator — Brushed Gold",
        "sku": "EE-AET-003",
        "price": 18900,
        "description": "Architectural double-bridge aviator crafted from aerospace-grade titanium with green G-15 polarized mineral glass lenses.",
        "image_url": "/static/images/frames/frame-3.webp",
        "category": "SUNGLASSES",
        "frame_shape": "AVIATOR",
        "frame_material": "TITANIUM",
        "lens_type": "POLARIZED",
        "stock": 9,
    },
    {
        "name": "Noir Palais — Obsidian Cat-Eye",
        "sku": "EE-NOI-004",
        "price": 15400,
        "description": "Sharp geometric cat-eye silhouette in high-gloss obsidian acetate with champagne gold core-wire detailing and UV400 gradient lenses.",
        "image_url": "/static/images/frames/frame-4.webp",
        "category": "SUNGLASSES",
        "frame_shape": "CAT_EYE",
        "frame_material": "ACETATE",
        "lens_type": "TINTED",
        "stock": 11,
    },
    {
        "name": "Zurich Architect — Raw Silver",
        "sku": "EE-ZUR-005",
        "price": 13800,
        "description": "Minimalist rimless-inspired optical frame in brushed Japanese titanium with blue-light filtering clarity for long studio sessions.",
        "image_url": "/static/images/frames/frame-5.webp",
        "category": "OPTICAL",
        "frame_shape": "RECTANGLE",
        "frame_material": "TITANIUM",
        "lens_type": "BLUE_LIGHT",
        "stock": 22,
    },
    {
        "name": "Sorrento Soleil — Champagne Crystal",
        "sku": "EE-SOR-006",
        "price": 14900,
        "description": "Translucent champagne acetate frame paired with emerald polarized lenses and custom nose pads for effortless Mediterranean wear.",
        "image_url": "/static/images/frames/frame-6.webp",
        "category": "SUNGLASSES",
        "frame_shape": "ROUND",
        "frame_material": "ACETATE",
        "lens_type": "POLARIZED",
        "stock": 15,
    },
    {
        "name": "Mayfair Scholar — Vintage Tortoise",
        "sku": "EE-MAY-007",
        "price": 12500,
        "description": "Keyhole bridge P3 optical silhouette crafted from cured tortoiseshell acetate with blue-violet anti-fatigue optical coatings.",
        "image_url": "/static/images/frames/frame-7.webp",
        "category": "OPTICAL",
        "frame_shape": "ROUND",
        "frame_material": "ACETATE",
        "lens_type": "BLUE_LIGHT",
        "stock": 19,
    },
    {
        "name": "Vanguard 78 — Gunmetal Aviator",
        "sku": "EE-VAN-008",
        "price": 17200,
        "description": "Precision-milled stainless steel aviator featuring flat nylon smoke lenses, spring temples, and laser-etched serial numbering.",
        "image_url": "/static/images/frames/frame-8.webp",
        "category": "SUNGLASSES",
        "frame_shape": "AVIATOR",
        "frame_material": "METAL",
        "lens_type": "POLARIZED",
        "stock": 8,
    },
    {
        "name": "Antwerp Studio — Espresso Square",
        "sku": "EE-ANT-009",
        "price": 13200,
        "description": "Bold architectural square optical frame in deep espresso acetate with exposed silver pins and blue-light filtering optics.",
        "image_url": "/static/images/frames/frame-9.webp",
        "category": "OPTICAL",
        "frame_shape": "SQUARE",
        "frame_material": "ACETATE",
        "lens_type": "BLUE_LIGHT",
        "stock": 16,
    },
    {
        "name": "Riviera 64 — Rose Gold Cat-Eye",
        "sku": "EE-RIV-010",
        "price": 15900,
        "description": "Ultra-thin electroplated rose gold metal frame with floating dusky-rose tinted lenses and weighted temple tips.",
        "image_url": "/static/images/frames/frame-10.webp",
        "category": "SUNGLASSES",
        "frame_shape": "CAT_EYE",
        "frame_material": "METAL",
        "lens_type": "TINTED",
        "stock": 12,
    },
    {
        "name": "Oslo Monolith — Matte Onyx",
        "sku": "EE-OSL-011",
        "price": 14600,
        "description": "Low-profile rectangular frame in sandblasted matte onyx acetate with high-contrast polarized slate lenses.",
        "image_url": "/static/images/frames/frame-11.webp",
        "category": "SUNGLASSES",
        "frame_shape": "RECTANGLE",
        "frame_material": "ACETATE",
        "lens_type": "POLARIZED",
        "stock": 14,
    },
    {
        "name": "Geneva Heritage — Gold Optical",
        "sku": "EE-GEN-012",
        "price": 16800,
        "description": "Octagonal-round hybrid optical frame in 18k gold-plated titanium with zero-distortion blue-light filter lenses.",
        "image_url": "/static/images/frames/frame-12.webp",
        "category": "OPTICAL",
        "frame_shape": "ROUND",
        "frame_material": "TITANIUM",
        "lens_type": "BLUE_LIGHT",
        "stock": 10,
    },
]

SAMPLE_REVIEWS = [
    (5, "Unbelievable balance on the nose bridge. Feels lighter than frames twice this price."),
    (5, "The lens clarity and leather case packaging rival Gentle Monster and Oliver Peoples."),
    (4, "Gorgeous acetate depth and zero glare while driving. Five-barrel hinges feel solid."),
    (5, "Wore these for 9 hours straight at my workstation—zero temple pressure or eye fatigue."),
    (5, "The brushed titanium finish catches the light subtly without looking flashy."),
    (4, "Crisp polarization and true-to-size bridge fit. Shipped quickly and well packed."),
    (5, "My optician was genuinely impressed by the Mazzucchelli acetate weight and polish."),
    (5, "Minimalist silhouette that pairs effortlessly with both formal and daily wear."),
]


def seed_database(db: Session) -> None:
    admin_email = os.getenv("ADMIN_EMAIL", "admin@easyeyes.com")
    admin_password = os.getenv("ADMIN_PASSWORD", "EasyEyes@Admin2026")
    customer_email = os.getenv("CUSTOMER_EMAIL", "arjun@easyeyes.com")
    customer_password = os.getenv("CUSTOMER_PASSWORD", "EasyEyes@User2026")

    admin = db.query(User).filter(User.email == admin_email).first()
    if not admin:
        admin = User(
            name="Curator (Admin)",
            email=admin_email,
            password_hash=hash_password(admin_password),
            role="ADMIN",
        )
        db.add(admin)

    customer1 = db.query(User).filter(User.email == customer_email).first()
    if not customer1:
        customer1 = User(
            name="Arjun Mehta",
            email=customer_email,
            password_hash=hash_password(customer_password),
            role="CUSTOMER",
        )
        db.add(customer1)

    customer2 = db.query(User).filter(User.email == "naina@easyeyes.com").first()
    if not customer2:
        customer2 = User(
            name="Naina Kapoor",
            email="naina@easyeyes.com",
            password_hash=hash_password(customer_password),
            role="CUSTOMER",
        )
        db.add(customer2)

    db.commit()
    db.refresh(customer1)
    db.refresh(customer2)

    for idx, item in enumerate(INITIAL_PRODUCTS):
        existing = db.query(Product).filter(Product.sku == item["sku"]).first()
        if not existing:
            product = Product(**item, rating_avg=0.0, review_count=0, is_active=True)
            db.add(product)
            db.flush()

            r1_rating, r1_comment = SAMPLE_REVIEWS[idx % len(SAMPLE_REVIEWS)]
            r2_rating, r2_comment = SAMPLE_REVIEWS[(idx + 3) % len(SAMPLE_REVIEWS)]

            db.add(Review(user_id=customer1.id, product_id=product.id, rating=r1_rating, comment=r1_comment))
            db.add(Review(user_id=customer2.id, product_id=product.id, rating=r2_rating, comment=r2_comment))

            product.review_count = 2
            product.rating_avg = round((r1_rating + r2_rating) / 2.0, 1)

    db.commit()
