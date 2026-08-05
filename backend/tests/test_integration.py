from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.main import app, get_db
from backend.app.database import Base, engine
import json
import time

# Setup TestClient
client = TestClient(app)

def test_auth_and_onboarding():
    # 1. Register a new buyer
    buyer_email = f"testbuyer_{time.time_ns()}@ankh.com"
    buyer_data = {
        "email": buyer_email,
        "password": "buyerpassword",
        "role": "buyer"
    }
    res_reg = client.post("/api/auth/register", json=buyer_data)
    assert res_reg.status_code == 201
    assert res_reg.json()["email"] == buyer_email
    assert res_reg.json()["role"] == "buyer"

    # 2. Login as buyer
    login_data = {
        "email": buyer_email,
        "password": "buyerpassword"
    }
    res_log = client.post("/api/auth/login", json=login_data)
    assert res_log.status_code == 200
    token = res_log.json()["access_token"]
    assert token is not None
    
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Get profile
    res_me = client.get("/api/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["email"] == buyer_email

    # 4. Onboard buyer
    onboard_buyer_data = {
        "business_type": "Retailer",
        "industry": "Apparel",
        "typical_order_qty": "500",
        "budget_range": "$10,000 - $50,000",
        "preferred_climate": "Tropical",
        "has_sensitive_skin": True,
        "skin_preferences": ["Hypoallergenic"]
    }
    res_onboard = client.post("/api/onboarding/buyer", json=onboard_buyer_data, headers=headers)
    if res_onboard.status_code != 200:
        print(f"Onboard Buyer failed: {res_onboard.status_code} - {res_onboard.text}")
    assert res_onboard.status_code == 200
    assert res_onboard.json()["status"] == "success"

def test_supplier_dashboard_and_products():
    # 1. Register a new supplier
    supplier_email = f"testsupplier_{time.time_ns()}@ankh.com"
    supplier_data = {
        "email": supplier_email,
        "password": "supplierpassword",
        "role": "supplier"
    }
    res_reg = client.post("/api/auth/register", json=supplier_data)
    assert res_reg.status_code == 201

    # 2. Login as supplier
    res_log = client.post("/api/auth/login", json={
        "email": supplier_email,
        "password": "supplierpassword"
    })
    assert res_log.status_code == 200
    token = res_log.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Complete supplier onboarding
    onboard_supplier_data = {
        "business_name": "Premium Linens LLC",
        "business_type": "Wholesaler",
        "contact_info": "wholesale@linens.com",
        "address": "45 Nile Street, Cairo",
        "operating_hours": "08:00 - 16:00 UTC",
        "categories": ["linen"]
    }
    res_onboard = client.post("/api/onboarding/supplier", json=onboard_supplier_data, headers=headers)
    assert res_onboard.status_code == 200

    # 4. Create a product that is out of stock (so it triggers inventory alerts)
    new_prod_data = {
        "id": "premium-linen-out",
        "brand": "Premium Linens LLC",
        "name": "Super Soft Handspun Linen",
        "in_stock": False,
        "gallery": ["https://images.unsplash.com/photo-1606744824163-985d376605aa"],
        "description": "Exquisite handspun linen fabric.",
        "price_amount": 140.00,
        "currency_symbol": "$",
        "gsm": 180,
        "breathability_rating": 5,
        "is_hypoallergenic": True,
        "texture_smoothness": 4,
        "oeko_tex_certified": True,
        "recommended_climate": ["Tropical", "Arid"]
    }
    res_create = client.post("/api/supplier/products", json=new_prod_data, headers=headers)
    assert res_create.status_code == 200

    # 5. Check supplier dashboard (verify serialization of gallery and recommended_climate list format)
    res_dash = client.get("/api/supplier/dashboard", headers=headers)
    assert res_dash.status_code == 200
    dash_data = res_dash.json()
    assert dash_data["total_products"] >= 1
    assert len(dash_data["inventory_alerts"]) >= 1
    alert_prod = dash_data["inventory_alerts"][0]
    assert alert_prod["id"] == "premium-linen-out"
    assert isinstance(alert_prod["gallery"], list)
    assert alert_prod["gallery"] == ["https://images.unsplash.com/photo-1606744824163-985d376605aa"]
    assert isinstance(alert_prod["recommended_climate"], list)
    assert alert_prod["recommended_climate"] == ["Tropical", "Arid"]

    # 6. Delete test product
    res_del = client.delete(f"/api/supplier/products/premium-linen-out", headers=headers)
    assert res_del.status_code == 200

def test_file_upload_and_product_creation():
    # 1. Register and login a supplier
    supplier_email = f"upload_supplier_{time.time_ns()}@ankh.com"
    res_reg = client.post("/api/auth/register", json={
        "email": supplier_email,
        "password": "supplierpassword",
        "role": "supplier"
    })
    assert res_reg.status_code == 201

    res_log = client.post("/api/auth/login", json={
        "email": supplier_email,
        "password": "supplierpassword"
    })
    assert res_log.status_code == 200
    token = res_log.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload a dummy image file to POST /api/upload
    dummy_file_content = b"fake-image-bytes-data-for-testing"
    files = {
        "file": ("test_fabric.jpg", dummy_file_content, "image/jpeg")
    }
    res_upload = client.post("/api/upload", files=files, headers=headers)
    assert res_upload.status_code == 200
    upload_json = res_upload.json()
    assert "url" in upload_json
    image_url = upload_json["url"]
    assert image_url.startswith("/static/uploads/")
    assert image_url.endswith(".jpg")

    # 3. Verify static file URL is served by backend
    res_static = client.get(image_url)
    assert res_static.status_code == 200
    assert res_static.content == dummy_file_content

    # 4. Create supplier product referencing uploaded image_url
    prod_id = f"upload-prod-{time.time_ns()}"
    new_prod = {
        "id": prod_id,
        "brand": "Upload Test Textiles",
        "name": "Custom Upload Fabric",
        "in_stock": True,
        "gallery": [image_url],
        "description": "Fabric with uploaded image.",
        "price_amount": 75.00,
        "currency_symbol": "$",
        "gsm": 200,
        "breathability_rating": 4,
        "is_hypoallergenic": True,
        "texture_smoothness": 4,
        "oeko_tex_certified": True,
        "recommended_climate": ["Temperate"]
    }
    res_create = client.post("/api/supplier/products", json=new_prod, headers=headers)
    assert res_create.status_code == 200

    # 5. Fetch product from public /api/products/{id} and verify gallery image URL
    res_get = client.get(f"/api/products/{prod_id}")
    assert res_get.status_code == 200
    prod_data = res_get.json()
    assert prod_data["gallery"] == [image_url]

    # Cleanup product
    res_del = client.delete(f"/api/supplier/products/{prod_id}", headers=headers)
    assert res_del.status_code == 200

if __name__ == "__main__":
    print("Running integration tests...")
    try:
        test_auth_and_onboarding()
        print("[PASS] test_auth_and_onboarding")
        test_supplier_dashboard_and_products()
        print("[PASS] test_supplier_dashboard_and_products")
        test_file_upload_and_product_creation()
        print("[PASS] test_file_upload_and_product_creation")
        print("All integration tests passed successfully!")
    except Exception as e:
        print(f"[FAIL] Tests failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
