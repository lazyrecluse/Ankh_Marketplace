from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def register(user: schemas.UserRegister, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pwd = security.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_pwd,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Initialize basic profiles based on role
    if user.role == "buyer":
        profile = models.BuyerProfile(user_id=new_user.id)
        db.add(profile)
    else:
        profile = models.SupplierProfile(user_id=new_user.id)
        db.add(profile)
    db.commit()

    return new_user


@router.post("/login", response_model=schemas.Token)
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not security.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    # Transparently upgrade hashes from the old custom pbkdf2 format to
    # the passlib-managed one, so we eventually don't need the legacy path.
    security._upgrade_hash_if_needed(db, db_user, user.password)

    access_token = security.create_access_token(data={"sub": db_user.email})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": db_user.role
    }


@router.get("/me")
def get_me(
    current_user: models.User = Depends(security.get_current_user),
    db: Session = Depends(get_db),
):
    res = {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
        "created_at": current_user.created_at
    }
    if current_user.role == "buyer":
        profile = db.query(models.BuyerProfile).filter(models.BuyerProfile.user_id == current_user.id).first()
        res["profile"] = {
            "business_type": profile.business_type if profile else None,
            "industry": profile.industry if profile else None,
            "typical_order_qty": profile.typical_order_qty if profile else None,
            "budget_range": profile.budget_range if profile else None,
            "preferred_climate": profile.preferred_climate if profile else None,
            "has_sensitive_skin": profile.has_sensitive_skin if profile else False,
            "skin_preferences": profile.skin_preferences if profile else []
        }
    else:
        profile = db.query(models.SupplierProfile).filter(models.SupplierProfile.user_id == current_user.id).first()
        res["profile"] = {
            "business_name": profile.business_name if profile else None,
            "business_type": profile.business_type if profile else None,
            "contact_info": profile.contact_info if profile else None,
            "address": profile.address if profile else None,
            "operating_hours": profile.operating_hours if profile else None,
            "categories": profile.categories if profile else []
        }
    return res
