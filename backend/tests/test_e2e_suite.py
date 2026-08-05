import io
import json
import os
import re
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
REPO_ROOT = Path(__file__).resolve().parents[2]

# ==============================================================================
# TIER 1: FEATURE COVERAGE (R1, R2, R3)
# ==============================================================================

# --- Feature R1: Local Image Upload & Static URL Serving ---

def test_r1_image_upload_valid_file():
    """
    R1.1 / R1.2: POST /api/upload should accept multipart image upload
    and return HTTP 200 with static URL path /static/uploads/<filename>.
    """
    dummy_content = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00\x48" # JPEG header
    files = {"file": ("test_fabric.jpg", io.BytesIO(dummy_content), "image/jpeg")}
    res = client.post("/api/upload", files=files)
    assert res.status_code == 200, f"Expected 200 OK from /api/upload, got {res.status_code}: {res.text}"
    data = res.json()
    url = data.get("url") or data.get("image_url")
    assert url is not None, "Response missing 'url' or 'image_url' key"
    assert url.startswith("/static/uploads/"), f"Image URL {url} does not start with /static/uploads/"


def test_r1_static_file_serving():
    """
    R1.1: Static file route /static/uploads/<filename> must serve uploaded image files over HTTP.
    """
    dummy_content = b"STATIC_IMAGE_TEST_BYTES_" + str(time.time_ns()).encode()
    files = {"file": ("static_serve_test.png", io.BytesIO(dummy_content), "image/png")}
    res_up = client.post("/api/upload", files=files)
    assert res_up.status_code == 200, f"Upload failed: {res_up.text}"
    url = res_up.json().get("url") or res_up.json().get("image_url")
    
    # Retrieve static file via TestClient
    res_get = client.get(url)
    assert res_get.status_code == 200, f"Failed to fetch static file from {url}: {res_get.status_code}"
    assert res_get.content == dummy_content, "Fetched static file content does not match uploaded content"


def test_r1_product_creation_with_uploaded_image():
    """
    R1.2 / R1.3: Supplier creates a product using an uploaded static image URL in gallery.
    """
    # 1. Register & login supplier
    supplier_email = f"r1_supplier_{time.time_ns()}@ankh.com"
    reg = client.post("/api/auth/register", json={"email": supplier_email, "password": "password123", "role": "supplier"})
    assert reg.status_code == 201
    log = client.post("/api/auth/login", json={"email": supplier_email, "password": "password123"})
    token = log.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Upload image
    dummy_content = b"FABRIC_PREVIEW_IMG"
    files = {"file": ("linen_preview.jpg", io.BytesIO(dummy_content), "image/jpeg")}
    up_res = client.post("/api/upload", files=files)
    assert up_res.status_code == 200
    img_url = up_res.json().get("url") or up_res.json().get("image_url")

    # 3. Create product with gallery containing uploaded image URL
    prod_id = f"r1-linen-{time.time_ns()}"
    prod_data = {
        "id": prod_id,
        "brand": "Nile Eco Weavers",
        "name": "Organic Egyptian Linen",
        "in_stock": True,
        "gallery": [img_url],
        "description": "High grade organic linen",
        "price_amount": 45.00,
        "currency_symbol": "$",
        "gsm": 160,
        "breathability_rating": 5,
        "is_hypoallergenic": True,
        "texture_smoothness": 4,
        "oeko_tex_certified": True,
        "recommended_climate": ["Tropical"]
    }
    res_create = client.post("/api/supplier/products", json=prod_data, headers=headers)
    assert res_create.status_code == 200

    # 4. Cleanup
    client.delete(f"/api/supplier/products/{prod_id}", headers=headers)


def test_r1_product_update_with_uploaded_image():
    """
    R1.3: Supplier updates an existing product gallery with an uploaded static image URL.
    """
    supplier_email = f"r1_supplier_upd_{time.time_ns()}@ankh.com"
    reg = client.post("/api/auth/register", json={"email": supplier_email, "password": "password123", "role": "supplier"})
    assert reg.status_code == 201
    token = client.post("/api/auth/login", json={"email": supplier_email, "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    prod_id = f"r1-upd-{time.time_ns()}"
    prod_data = {
        "id": prod_id,
        "brand": "Nile Mills",
        "name": "Raw Cotton Weave",
        "in_stock": True,
        "gallery": ["https://placeholder.com/initial.jpg"],
        "description": "Raw cotton fabric",
        "price_amount": 25.00,
        "currency_symbol": "$",
        "gsm": 140,
        "breathability_rating": 4,
        "is_hypoallergenic": False,
        "texture_smoothness": 3,
        "oeko_tex_certified": False,
        "recommended_climate": ["Temperate"]
    }
    client.post("/api/supplier/products", json=prod_data, headers=headers)

    # Upload new image
    files = {"file": ("new_cotton.jpg", io.BytesIO(b"NEW_COTTON_IMG"), "image/jpeg")}
    up_res = client.post("/api/upload", files=files)
    assert up_res.status_code == 200
    new_img_url = up_res.json().get("url") or up_res.json().get("image_url")

    # Update product with uploaded URL
    prod_data["gallery"] = [new_img_url]
    res_upd = client.put(f"/api/supplier/products/{prod_id}", json=prod_data, headers=headers)
    assert res_upd.status_code == 200

    # Verify update via GET
    res_get = client.get(f"/api/products/{prod_id}")
    assert res_get.status_code == 200
    assert new_img_url in res_get.json()["gallery"]

    client.delete(f"/api/supplier/products/{prod_id}", headers=headers)


def test_r1_product_gallery_relative_url_retrieval():
    """
    R1.3: Product catalog endpoint GET /api/products/{id} returns static relative URL in gallery array.
    """
    supplier_email = f"r1_supplier_gal_{time.time_ns()}@ankh.com"
    client.post("/api/auth/register", json={"email": supplier_email, "password": "password123", "role": "supplier"})
    token = client.post("/api/auth/login", json={"email": supplier_email, "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    static_url = f"/static/uploads/fabric_{time.time_ns()}.png"
    prod_id = f"r1-gal-{time.time_ns()}"
    prod_data = {
        "id": prod_id,
        "brand": "Lux Silk",
        "name": "Mulberry Silk Brocade",
        "in_stock": True,
        "gallery": [static_url],
        "description": "Luxurious mulberry silk",
        "price_amount": 120.00,
        "currency_symbol": "$",
        "gsm": 90,
        "breathability_rating": 4,
        "is_hypoallergenic": True,
        "texture_smoothness": 5,
        "oeko_tex_certified": True,
        "recommended_climate": ["Temperate"]
    }
    client.post("/api/supplier/products", json=prod_data, headers=headers)

    res = client.get(f"/api/products/{prod_id}")
    assert res.status_code == 200
    gallery = res.json()["gallery"]
    assert len(gallery) >= 1
    assert gallery[0] == static_url

    client.delete(f"/api/supplier/products/{prod_id}", headers=headers)


# --- Feature R2: Dedicated Buyer Sign-in Flow & Auth ---

def test_r2_buyer_registration():
    """
    R2.1 / R2.2: POST /api/auth/register registers a buyer user with role='buyer'.
    """
    buyer_email = f"r2_reg_buyer_{time.time_ns()}@ankh.com"
    res = client.post("/api/auth/register", json={"email": buyer_email, "password": "securepassword", "role": "buyer"})
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == buyer_email
    assert data["role"] == "buyer"


def test_r2_buyer_login_success():
    """
    R2.1 / R2.2: POST /api/auth/login authenticates buyer user and returns JWT access_token & role='buyer'.
    """
    buyer_email = f"r2_log_buyer_{time.time_ns()}@ankh.com"
    client.post("/api/auth/register", json={"email": buyer_email, "password": "buyerpass123", "role": "buyer"})
    
    res = client.post("/api/auth/login", json={"email": buyer_email, "password": "buyerpass123"})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data.get("role") == "buyer"


def test_r2_buyer_profile_fetch():
    """
    R2.2: GET /api/auth/me returns buyer user info and initialized buyer profile schema.
    """
    buyer_email = f"r2_me_buyer_{time.time_ns()}@ankh.com"
    client.post("/api/auth/register", json={"email": buyer_email, "password": "buyerpass123", "role": "buyer"})
    log = client.post("/api/auth/login", json={"email": buyer_email, "password": "buyerpass123"})
    token = log.json()["access_token"]

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["email"] == buyer_email
    assert data["role"] == "buyer"
    assert "profile" in data


def test_r2_buyer_onboarding_submission():
    """
    R2.2: POST /api/onboarding/buyer saves buyer business profile & preferences.
    """
    buyer_email = f"r2_onboard_buyer_{time.time_ns()}@ankh.com"
    client.post("/api/auth/register", json={"email": buyer_email, "password": "buyerpass123", "role": "buyer"})
    token = client.post("/api/auth/login", json={"email": buyer_email, "password": "buyerpass123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    onboard_payload = {
        "business_type": "Apparel Brand",
        "industry": "Luxury Fashion",
        "typical_order_qty": "1000m",
        "budget_range": "$50,000 - $100,000",
        "preferred_climate": "Temperate",
        "has_sensitive_skin": True,
        "skin_preferences": ["Hypoallergenic", "Organic"]
    }
    res = client.post("/api/onboarding/buyer", json=onboard_payload, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "success"

    me = client.get("/api/auth/me", headers=headers).json()
    assert me["profile"]["business_type"] == "Apparel Brand"
    assert me["profile"]["has_sensitive_skin"] is True


def test_r2_buyer_login_invalid_credentials():
    """
    R2.2: POST /api/auth/login rejects incorrect passwords with HTTP 400.
    """
    buyer_email = f"r2_bad_login_{time.time_ns()}@ankh.com"
    client.post("/api/auth/register", json={"email": buyer_email, "password": "correctpassword", "role": "buyer"})
    
    res = client.post("/api/auth/login", json={"email": buyer_email, "password": "wrongpassword"})
    assert res.status_code == 400
    assert "Incorrect email or password" in res.json()["detail"]


# --- Feature R3: Navigation Bar Clearance Padding (SCSS Code AST Inspection) ---

def test_r3_css_auth_container_padding():
    """
    R3.1: .auth-container in src/Pages/Auth/AuthPage.scss must have padding-top >= 100px
    to clear the fixed 80px navigation bar.
    """
    scss_path = REPO_ROOT / "src" / "Pages" / "Auth" / "AuthPage.scss"
    assert scss_path.exists(), f"AuthPage.scss missing at {scss_path}"
    content = scss_path.read_text()

    # Search for .auth-container block and check padding/padding-top
    match = re.search(r"\.auth-container\s*\{([^}]+)\}", content)
    assert match is not None, ".auth-container selector not found in AuthPage.scss"
    block = match.group(1)
    
    pad_match = re.search(r"padding(?:-top)?\s*:\s*(\d+)px", block)
    assert pad_match is not None, "padding or padding-top property missing in .auth-container"
    pad_val = int(pad_match.group(1))
    assert pad_val >= 100, f".auth-container padding-top is {pad_val}px, required >= 100px to clear navbar"


def test_r3_css_onboard_container_padding():
    """
    R3.1: .onboard-container in src/Pages/Onboarding/Onboarding.scss must have padding-top >= 100px
    to clear the fixed 80px navigation bar.
    """
    scss_path = REPO_ROOT / "src" / "Pages" / "Onboarding" / "Onboarding.scss"
    assert scss_path.exists(), f"Onboarding.scss missing at {scss_path}"
    content = scss_path.read_text()

    match = re.search(r"\.onboard-container\s*\{([^}]+)\}", content)
    assert match is not None, ".onboard-container selector not found in Onboarding.scss"
    block = match.group(1)
    
    pad_match = re.search(r"padding(?:-top)?\s*:\s*(\d+)px", block)
    assert pad_match is not None, "padding or padding-top property missing in .onboard-container"
    pad_val = int(pad_match.group(1))
    assert pad_val >= 100, f".onboard-container padding-top is {pad_val}px, required >= 100px to clear navbar"


def test_r3_css_dashboard_container_padding():
    """
    R3.1: .dashboard-container in src/Pages/Dashboard/Dashboard.scss must have padding-top >= 100px
    to clear the fixed 80px navigation bar.
    """
    scss_path = REPO_ROOT / "src" / "Pages" / "Dashboard" / "Dashboard.scss"
    assert scss_path.exists(), f"Dashboard.scss missing at {scss_path}"
    content = scss_path.read_text()

    match = re.search(r"\.dashboard-container\s*\{([^}]+)\}", content)
    assert match is not None, ".dashboard-container selector not found in Dashboard.scss"
    block = match.group(1)
    
    pad_match = re.search(r"padding(?:-top)?\s*:\s*(\d+)px", block)
    assert pad_match is not None, "padding or padding-top property missing in .dashboard-container"
    pad_val = int(pad_match.group(1))
    assert pad_val >= 100, f".dashboard-container padding-top is {pad_val}px, required >= 100px to clear navbar"


def test_r3_navbar_fixed_height_clearance():
    """
    R3.1: Verify total padding-top across layout containers guarantees complete clearance of fixed 80px navbar.
    """
    files_to_check = [
        REPO_ROOT / "src" / "Pages" / "Auth" / "AuthPage.scss",
        REPO_ROOT / "src" / "Pages" / "Onboarding" / "Onboarding.scss",
        REPO_ROOT / "src" / "Pages" / "Dashboard" / "Dashboard.scss"
    ]
    insufficient_containers = []
    for file_path in files_to_check:
        content = file_path.read_text()
        for selector in [".auth-container", ".onboard-container", ".dashboard-container"]:
            if selector in content:
                match = re.search(re.escape(selector) + r"\s*\{([^}]+)\}", content)
                if match:
                    block = match.group(1)
                    pad_match = re.search(r"padding(?:-top)?\s*:\s*(\d+)px", block)
                    val = int(pad_match.group(1)) if pad_match else 0
                    if val < 100:
                        insufficient_containers.append((selector, file_path.name, val))
    
    assert len(insufficient_containers) == 0, f"Containers with top padding < 100px: {insufficient_containers}"


def test_r3_frontend_buyer_route_configuration():
    """
    R2.1 / R3.1: Verify App.js configures route support for AuthPage (/login or /login/buyer).
    """
    app_js = REPO_ROOT / "src" / "App" / "App.js"
    assert app_js.exists()
    content = app_js.read_text()
    assert 'path="/login"' in content or 'path="/login/buyer"' in content, "App.js router missing login path"


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES
# ==============================================================================

def test_tier2_upload_empty_file():
    """
    Tier 2: POST /api/upload with zero-byte empty file.
    """
    empty_file = {"file": ("empty.jpg", io.BytesIO(b""), "image/jpeg")}
    res = client.post("/api/upload", files=empty_file)
    # The endpoint should either handle 0-byte upload safely returning 200 or return 400 Bad Request
    assert res.status_code in [200, 400], f"Unexpected status code for empty file upload: {res.status_code}"


def test_tier2_upload_unusual_file_extension():
    """
    Tier 2: POST /api/upload with non-standard extensions (.webp, .tiff, .svg).
    """
    unusual_file = {"file": ("sample.webp", io.BytesIO(b"WEBP_BYTES"), "image/webp")}
    res = client.post("/api/upload", files=unusual_file)
    assert res.status_code == 200
    url = res.json().get("url") or res.json().get("image_url")
    assert url.endswith(".webp") or "/static/uploads/" in url


def test_tier2_register_duplicate_email():
    """
    Tier 2: Registering an already existing email address returns HTTP 400.
    """
    email = f"dup_{time.time_ns()}@ankh.com"
    r1 = client.post("/api/auth/register", json={"email": email, "password": "pass", "role": "buyer"})
    assert r1.status_code == 201

    r2 = client.post("/api/auth/register", json={"email": email, "password": "pass", "role": "buyer"})
    assert r2.status_code == 400
    assert "Email already registered" in r2.json()["detail"]


def test_tier2_supplier_onboarding_forbidden_for_buyer():
    """
    Tier 2: A user registered as 'buyer' attempting POST /api/onboarding/supplier receives 403 Forbidden.
    """
    email = f"buyer_to_supplier_{time.time_ns()}@ankh.com"
    client.post("/api/auth/register", json={"email": email, "password": "pass", "role": "buyer"})
    token = client.post("/api/auth/login", json={"email": email, "password": "pass"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    supplier_onboard_data = {
        "business_name": "Unauthorized Inc",
        "business_type": "Weaver",
        "contact_info": "contact@unauth.com",
        "address": "123 Nile St",
        "operating_hours": "09:00 - 17:00",
        "categories": ["cotton"]
    }
    res = client.post("/api/onboarding/supplier", json=supplier_onboard_data, headers=headers)
    assert res.status_code == 403
    assert "Only suppliers" in res.json()["detail"]


def test_tier2_supplier_product_creation_invalid_payload():
    """
    Tier 2: Creating a product missing required fields returns 422 Unprocessable Entity.
    """
    email = f"supplier_invalid_prod_{time.time_ns()}@ankh.com"
    client.post("/api/auth/register", json={"email": email, "password": "pass", "role": "supplier"})
    token = client.post("/api/auth/login", json={"email": email, "password": "pass"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Missing price_amount and brand
    invalid_payload = {
        "id": f"invalid-prod-{time.time_ns()}",
        "name": "Incomplete Fabric"
    }
    res = client.post("/api/supplier/products", json=invalid_payload, headers=headers)
    assert res.status_code == 422


# ==============================================================================
# TIER 3: CROSS-FEATURE INTERACTIONS
# ==============================================================================

def test_tier3_buyer_auth_to_product_browsing():
    """
    Tier 3: Flow: Buyer registers -> logs in -> fetches profile -> queries products by climate filter.
    """
    email = f"buyer_flow_{time.time_ns()}@ankh.com"
    reg = client.post("/api/auth/register", json={"email": email, "password": "buyerpass123", "role": "buyer"})
    assert reg.status_code == 201

    log = client.post("/api/auth/login", json={"email": email, "password": "buyerpass123"})
    token = log.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "buyer"

    prods = client.get("/api/products?climate=Tropical")
    assert prods.status_code == 200
    assert isinstance(prods.json(), list)


def test_tier3_supplier_auth_image_upload_product_creation():
    """
    Tier 3: Flow: Supplier registers -> logs in -> uploads static image -> creates product with image -> checks dashboard.
    """
    supplier_email = f"supplier_flow_{time.time_ns()}@ankh.com"
    client.post("/api/auth/register", json={"email": supplier_email, "password": "supplierpass", "role": "supplier"})
    token = client.post("/api/auth/login", json={"email": supplier_email, "password": "supplierpass"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload Image
    files = {"file": ("fabric_sample.jpg", io.BytesIO(b"FABRIC_SAMPLE_IMAGE"), "image/jpeg")}
    up_res = client.post("/api/upload", files=files)
    assert up_res.status_code == 200
    img_url = up_res.json().get("url") or up_res.json().get("image_url")

    # Create Product
    prod_id = f"tier3-prod-{time.time_ns()}"
    prod = {
        "id": prod_id,
        "brand": "Flow Weavers",
        "name": "Egyptian Heavy Twill",
        "in_stock": True,
        "gallery": [img_url],
        "description": "Heavy twill fabric",
        "price_amount": 55.00,
        "currency_symbol": "$",
        "gsm": 220,
        "breathability_rating": 3,
        "is_hypoallergenic": True,
        "texture_smoothness": 4,
        "oeko_tex_certified": True,
        "recommended_climate": ["Temperate"]
    }
    create_res = client.post("/api/supplier/products", json=prod, headers=headers)
    assert create_res.status_code == 200

    # Verify Supplier Dashboard
    dash_res = client.get("/api/supplier/dashboard", headers=headers)
    assert dash_res.status_code == 200
    assert dash_res.json()["total_products"] >= 1

    client.delete(f"/api/supplier/products/{prod_id}", headers=headers)


def test_tier3_supplier_image_upload_and_buyer_gallery_view():
    """
    Tier 3: Flow: Supplier uploads image and creates product; Buyer fetches product details and sees static uploaded image URL.
    """
    supplier_email = f"supplier_gal_flow_{time.time_ns()}@ankh.com"
    client.post("/api/auth/register", json={"email": supplier_email, "password": "supplierpass", "role": "supplier"})
    s_token = client.post("/api/auth/login", json={"email": supplier_email, "password": "supplierpass"}).json()["access_token"]
    s_headers = {"Authorization": f"Bearer {s_token}"}

    # Upload Image
    files = {"file": ("b2b_gallery_test.jpg", io.BytesIO(b"GALLERY_BYTES"), "image/jpeg")}
    up_res = client.post("/api/upload", files=files)
    assert up_res.status_code == 200
    uploaded_url = up_res.json().get("url") or up_res.json().get("image_url")

    # Create Product
    prod_id = f"b2b-gal-{time.time_ns()}"
    prod = {
        "id": prod_id,
        "brand": "Cross Weave Co",
        "name": "B2B Fine Canvas",
        "in_stock": True,
        "gallery": [uploaded_url],
        "description": "Fine canvas material",
        "price_amount": 35.00,
        "currency_symbol": "$",
        "gsm": 280,
        "breathability_rating": 2,
        "is_hypoallergenic": False,
        "texture_smoothness": 3,
        "oeko_tex_certified": False,
        "recommended_climate": ["Polar"]
    }
    client.post("/api/supplier/products", json=prod, headers=s_headers)

    # Buyer inspects product catalog
    prod_detail = client.get(f"/api/products/{prod_id}")
    assert prod_detail.status_code == 200
    assert uploaded_url in prod_detail.json()["gallery"]

    client.delete(f"/api/supplier/products/{prod_id}", headers=s_headers)


# ==============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS
# ==============================================================================

def test_tier4_full_marketplace_lifecycle():
    """
    Tier 4: End-to-End Real World Scenario:
    1. Supplier registers, logs in, uploads image, creates fabric product.
    2. Buyer registers, logs in, completes onboarding.
    3. Buyer browses catalog & places order.
    4. Supplier views order on dashboard & updates status to 'Preparing' -> 'Completed'.
    5. Buyer verifies completed order status.
    """
    ts = time.time_ns()
    supplier_email = f"lifecycle_supplier_{ts}@ankh.com"
    buyer_email = f"lifecycle_buyer_{ts}@ankh.com"

    # 1. Supplier Auth & Upload
    client.post("/api/auth/register", json={"email": supplier_email, "password": "password123", "role": "supplier"})
    s_token = client.post("/api/auth/login", json={"email": supplier_email, "password": "password123"}).json()["access_token"]
    s_headers = {"Authorization": f"Bearer {s_token}"}

    up_res = client.post("/api/upload", files={"file": ("lifecycle_fabric.jpg", io.BytesIO(b"LIFECYCLE_IMG"), "image/jpeg")})
    assert up_res.status_code == 200
    img_url = up_res.json().get("url") or up_res.json().get("image_url")

    prod_id = f"lifecycle-prod-{ts}"
    prod_data = {
        "id": prod_id,
        "brand": "Lifecycle Mills",
        "name": "Lifecycle Linen Blend",
        "in_stock": True,
        "gallery": [img_url],
        "description": "Premium linen blend",
        "price_amount": 60.00,
        "currency_symbol": "$",
        "gsm": 190,
        "breathability_rating": 4,
        "is_hypoallergenic": True,
        "texture_smoothness": 4,
        "oeko_tex_certified": True,
        "recommended_climate": ["Temperate"]
    }
    res_p = client.post("/api/supplier/products", json=prod_data, headers=s_headers)
    assert res_p.status_code == 200

    # 2. Buyer Auth & Onboarding
    client.post("/api/auth/register", json={"email": buyer_email, "password": "password123", "role": "buyer"})
    b_token = client.post("/api/auth/login", json={"email": buyer_email, "password": "password123"}).json()["access_token"]
    b_headers = {"Authorization": f"Bearer {b_token}"}

    client.post("/api/onboarding/buyer", json={
        "business_type": "Boutique",
        "industry": "Apparel",
        "typical_order_qty": "500m",
        "budget_range": "$10,000 - $20,000",
        "preferred_climate": "Temperate",
        "has_sensitive_skin": True,
        "skin_preferences": ["Hypoallergenic"]
    }, headers=b_headers)

    # 3. Buyer Places Order
    order_payload = {
        "shipping_name": "Jane Buyer",
        "shipping_address": "100 Fashion Ave",
        "shipping_city": "Cairo",
        "shipping_country": "Egypt",
        "total_price": 1200.00,
        "currency_symbol": "$",
        "items": [
            {
                "product_id": prod_id,
                "quantity": 20,
                "price_amount": 60.00
            }
        ]
    }
    res_order = client.post("/api/orders", json=order_payload, headers=b_headers)
    assert res_order.status_code == 200
    order_id = res_order.json()["order_id"]

    # 4. Supplier Checks Dashboard & Updates Order Status
    s_orders = client.get("/api/supplier/orders", headers=s_headers).json()
    assert len(s_orders) >= 1
    found_order = next((o for o in s_orders if o["id"] == order_id), None)
    assert found_order is not None

    upd_status = client.put(f"/api/supplier/orders/{order_id}/status", json={"status": "Completed"}, headers=s_headers)
    assert upd_status.status_code == 200

    # 5. Buyer Verifies Updated Order Status
    b_orders = client.get("/api/buyer/orders", headers=b_headers).json()
    my_order = next((o for o in b_orders if o["id"] == order_id), None)
    assert my_order is not None
    assert my_order["status"] == "Completed"

    # Cleanup
    client.delete(f"/api/supplier/products/{prod_id}", headers=s_headers)


def test_tier4_supplier_inventory_alert_with_uploaded_image():
    """
    Tier 4: Supplier creates an out-of-stock product with uploaded static image URL
    and verifies that it properly triggers inventory alert list on supplier dashboard.
    """
    ts = time.time_ns()
    supplier_email = f"alert_supplier_{ts}@ankh.com"
    client.post("/api/auth/register", json={"email": supplier_email, "password": "password123", "role": "supplier"})
    token = client.post("/api/auth/login", json={"email": supplier_email, "password": "password123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Upload Image
    up_res = client.post("/api/upload", files={"file": ("alert_fabric.jpg", io.BytesIO(b"ALERT_IMG"), "image/jpeg")})
    assert up_res.status_code == 200
    img_url = up_res.json().get("url") or up_res.json().get("image_url")

    # Create Out-of-Stock Product (in_stock = False)
    prod_id = f"alert-prod-{ts}"
    prod_data = {
        "id": prod_id,
        "brand": "Out of Stock Mills",
        "name": "Rare Egyptian Flax Linen",
        "in_stock": False,
        "gallery": [img_url],
        "description": "Currently sold out rare linen",
        "price_amount": 150.00,
        "currency_symbol": "$",
        "gsm": 200,
        "breathability_rating": 5,
        "is_hypoallergenic": True,
        "texture_smoothness": 5,
        "oeko_tex_certified": True,
        "recommended_climate": ["Tropical"]
    }
    client.post("/api/supplier/products", json=prod_data, headers=headers)

    # Inspect Dashboard Inventory Alerts
    dash = client.get("/api/supplier/dashboard", headers=headers)
    assert dash.status_code == 200
    alerts = dash.json()["inventory_alerts"]
    assert len(alerts) >= 1
    alert_ids = [a["id"] for a in alerts]
    assert prod_id in alert_ids

    client.delete(f"/api/supplier/products/{prod_id}", headers=headers)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
