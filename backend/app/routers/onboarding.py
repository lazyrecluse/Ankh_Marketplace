from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/onboarding", tags=["Onboarding"])


@router.post("/buyer")
def onboarding_buyer(
    profile_data: schemas.BuyerOnboarding,
    current_user: models.User = Depends(security.require_buyer),
    db: Session = Depends(get_db),
):
    profile = db.query(models.BuyerProfile).filter(models.BuyerProfile.user_id == current_user.id).first()
    if not profile:
        profile = models.BuyerProfile(user_id=current_user.id)
        db.add(profile)

    profile.business_type = profile_data.business_type
    profile.industry = profile_data.industry
    profile.typical_order_qty = profile_data.typical_order_qty
    profile.budget_range = profile_data.budget_range
    profile.preferred_climate = profile_data.preferred_climate
    profile.has_sensitive_skin = profile_data.has_sensitive_skin
    profile.skin_preferences = profile_data.skin_preferences

    db.commit()
    return {"status": "success", "message": "Buyer onboarding completed successfully"}


@router.post("/supplier")
def onboarding_supplier(
    profile_data: schemas.SupplierOnboarding,
    current_user: models.User = Depends(security.require_supplier),
    db: Session = Depends(get_db),
):
    profile = db.query(models.SupplierProfile).filter(models.SupplierProfile.user_id == current_user.id).first()
    if not profile:
        profile = models.SupplierProfile(user_id=current_user.id)
        db.add(profile)

    profile.business_name = profile_data.business_name
    profile.business_type = profile_data.business_type
    profile.contact_info = profile_data.contact_info
    profile.address = profile_data.address
    profile.operating_hours = profile_data.operating_hours
    profile.categories = profile_data.categories

    db.commit()
    return {"status": "success", "message": "Supplier onboarding completed successfully"}
