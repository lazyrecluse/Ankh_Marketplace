import React, { useState, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import {
    getDashboard,
    getSupplierOrders,
    updateOrderStatus,
    createProduct,
    updateProduct,
    deleteProduct,
    uploadImage
} from '../../Api/supplier';
import { getMe } from '../../Api/auth';
import { getProducts } from '../../Api/catalog';
import { resolveImageUrl } from '../../Api/client';
import * as session from '../../Auth/session';
import './Dashboard.scss';

export default function SupplierDashboard() {
    const history = useHistory();
    const [dashboardMetrics, setDashboardMetrics] = useState(null);
    const [orders, setOrders] = useState([]);
    const [products, setProducts] = useState([]);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Inventory Modal/Form state
    const [showAddForm, setShowAddForm] = useState(false);
    const [editingProduct, setEditingProduct] = useState(null);
    
    // Product form fields
    const [pId, setPId] = useState('');
    const [pBrand, setPBrand] = useState('');
    const [pName, setPName] = useState('');
    const [pInStock, setPInStock] = useState(true);
    const [pGallery, setPGallery] = useState('');
    const [pDesc, setPDesc] = useState('');
    const [pPrice, setPPrice] = useState('');
    const [pCurrency, setPCurrency] = useState('$');
    const [pGsm, setPGsm] = useState('');
    const [pBreathability, setPBreathability] = useState(3);
    const [pHypoallergenic, setPHypoallergenic] = useState(false);
    const [pSmoothness, setPSmoothness] = useState(3);
    const [pOekoTex, setPOekoTex] = useState(false);
    const [pClimates, setPClimates] = useState([]);
    const [uploading, setUploading] = useState(false);

    const handleFileUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploading(true);
        try {
            const uploadedUrl = await uploadImage(file);
            if (uploadedUrl) {
                setPGallery((prev) => (prev ? `${prev}\n${uploadedUrl}` : uploadedUrl));
            }
        } catch (err) {
            alert(`Upload error: ${err.message}`);
        } finally {
            setUploading(false);
            e.target.value = '';
        }
    };

    const fetchAllSupplierData = async () => {
        if (!session.isLoggedIn()) {
            history.push('/login');
            return;
        }

        try {
            const meData = await getMe();
            setUser(meData);

            const statsData = await getDashboard();
            setDashboardMetrics(statsData);

            const ordersData = await getSupplierOrders();
            setOrders(ordersData);

            const productsData = await getProducts({ supplier_id: meData.id });
            setProducts(productsData);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchAllSupplierData();
    }, [history]);

    const handleLogout = () => {
        // Clears only the auth keys; the persisted Redux cart survives.
        session.clearSession();
        window.location.href = '/login';
    };

    // Update incoming order status, then refresh so the row reflects the
    // persisted value rather than the optimistic select state.
    const handleOrderStatusChange = async (orderId, newStatus) => {
        try {
            await updateOrderStatus(orderId, newStatus);
            await fetchAllSupplierData();
        } catch (err) {
            alert(err.message);
        }
    };

    // Add or Edit Product Form Submission
    const handleProductSubmit = async (e) => {
        e.preventDefault();

        // Clean formats
        const galleryList = pGallery.split('\n').filter(url => url.trim() !== '');

        const body = {
            id: pId,
            brand: pBrand,
            name: pName,
            in_stock: pInStock,
            gallery: galleryList,
            description: pDesc,
            price_amount: parseFloat(pPrice),
            currency_symbol: pCurrency,
            gsm: parseInt(pGsm) || 150,
            breathability_rating: parseInt(pBreathability),
            is_hypoallergenic: pHypoallergenic,
            texture_smoothness: parseInt(pSmoothness),
            oeko_tex_certified: pOekoTex,
            recommended_climate: pClimates
        };

        try {
            if (editingProduct) {
                await updateProduct(editingProduct.id, body);
            } else {
                await createProduct(body);
            }

            setShowAddForm(false);
            setEditingProduct(null);
            resetForm();
            fetchAllSupplierData();
        } catch (err) {
            alert(err.message);
        }
    };

    const handleDeleteProduct = async (prodId) => {
        if (!window.confirm("Are you sure you want to delete this fabric product from your catalog?")) return;
        try {
            await deleteProduct(prodId);
            fetchAllSupplierData();
        } catch (err) {
            alert(err.message);
        }
    };

    const openEditForm = (p) => {
        setEditingProduct(p);
        setPId(p.id);
        setPBrand(p.brand);
        setPName(p.name);
        setPInStock(p.inStock);
        setPGallery(p.gallery.join('\n'));
        setPDesc(p.description || '');
        // handle price parsing
        setPPrice(p.prices[0]?.amount || '');
        setPCurrency(p.prices[0]?.currency?.symbol || '$');
        setPGsm(p.gsm || '');
        setPBreathability(p.breathability_rating || 3);
        setPHypoallergenic(p.is_hypoallergenic || false);
        setPSmoothness(p.texture_smoothness || 3);
        setPOekoTex(p.oeko_tex_certified || false);
        setPClimates(p.recommended_climate || []);
        setShowAddForm(true);
    };

    const toggleClimateSelection = (climate) => {
        if (pClimates.includes(climate)) {
            setPClimates(pClimates.filter(c => c !== climate));
        } else {
            setPClimates([...pClimates, climate]);
        }
    };

    const resetForm = () => {
        setPId('');
        setPBrand('');
        setPName('');
        setPInStock(true);
        setPGallery('');
        setPDesc('');
        setPPrice('');
        setPGsm('');
        setPBreathability(3);
        setPHypoallergenic(false);
        setPSmoothness(3);
        setPOekoTex(false);
        setPClimates([]);
    };

    if (loading) return <div className="dashboard-loading">Loading Supplier Dashboard...</div>;

    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <div>
                    <h1>Supplier Control Center</h1>
                    <p className="welcome">Business Name: <strong>{user?.profile?.business_name}</strong> ({user?.profile?.business_type})</p>
                </div>
                <div className="header-actions">
                    <button className="btn-logout" onClick={handleLogout}>Log Out</button>
                </div>
            </header>

            {error && <div className="dashboard-alert error">{error}</div>}

            {/* Metrics Row */}
            <section className="metrics-row">
                <div className="metric-card">
                    <span className="metric-label">Total Products</span>
                    <span className="metric-val">{dashboardMetrics?.total_products || 0}</span>
                </div>
                <div className="metric-card">
                    <span className="metric-label">In Stock / Active</span>
                    <span className="metric-val">{dashboardMetrics?.active_products || 0}</span>
                </div>
                <div className="metric-card alert">
                    <span className="metric-label">Pending Orders</span>
                    <span className="metric-val">{dashboardMetrics?.pending_orders || 0}</span>
                </div>
                <div className="metric-card warning">
                    <span className="metric-label">Out of Stock Alerts</span>
                    <span className="metric-val">{dashboardMetrics?.inventory_alerts?.length || 0}</span>
                </div>
            </section>

            <div className="dashboard-layout">
                {/* Left side: Orders */}
                <main className="dashboard-content flex-2">
                    <div className="card orders-card">
                        <h3>Incoming B2B Orders</h3>
                        {orders.length === 0 ? (
                            <div className="empty-state">No client orders received yet.</div>
                        ) : (
                            <div className="orders-table-wrapper">
                                <table className="orders-table">
                                    <thead>
                                        <tr>
                                            <th>Order ID</th>
                                            <th>Date</th>
                                            <th>Buyer</th>
                                            <th>Items Requested</th>
                                            <th>Total Price</th>
                                            <th>Status</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {orders.map((o) => (
                                            <tr key={o.id}>
                                                <td>#{o.id}</td>
                                                <td>{new Date(o.created_at).toLocaleDateString()}</td>
                                                <td>{o.shipping_name}</td>
                                                <td>
                                                    <ul className="items-list">
                                                        {o.items.map((item, idx) => (
                                                            <li key={idx}>{item.product_name} ({item.quantity} units)</li>
                                                        ))}
                                                    </ul>
                                                </td>
                                                <td>{o.currency_symbol}{parseFloat(o.total_price).toFixed(2)}</td>
                                                <td>
                                                    <span className={`status-badge ${o.status.toLowerCase().replace(/\s+/g, '-')}`}>
                                                        {o.status}
                                                    </span>
                                                </td>
                                                <td>
                                                    <div className="status-dropdown-group">
                                                        <select 
                                                            value={o.status}
                                                            onChange={(e) => handleOrderStatusChange(o.id, e.target.value)}
                                                        >
                                                            <option value="Pending">Pending</option>
                                                            <option value="Accepted">Accepted</option>
                                                            <option value="Preparing">Preparing</option>
                                                            <option value="Ready for Dispatch">Ready for Dispatch</option>
                                                            <option value="Completed">Completed</option>
                                                        </select>
                                                    </div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </main>

                {/* Right side: Catalog/Inventory Control */}
                <aside className="dashboard-sidebar flex-1">
                    <div className="card catalog-card">
                        <div className="card-header-flex">
                            <h3>Fabric Catalog</h3>
                            <button className="btn-primary-sm" onClick={() => { setEditingProduct(null); resetForm(); setShowAddForm(true); }}>
                                + Add Fabric
                            </button>
                        </div>

                        {products.length === 0 ? (
                            <div className="empty-state">No fabrics listed yet. Add your first product.</div>
                        ) : (
                            <div className="supplier-products-list">
                                {products.map((p) => (
                                    <div key={p.id} className="supplier-product-item">
                                        <img src={resolveImageUrl(p.gallery?.[0], 'https://via.placeholder.com/80')} alt={p.name} />
                                        <div className="product-info-mini">
                                            <h4>{p.name}</h4>
                                            <p className="text-muted">{p.brand} • {p.prices[0]?.currency?.symbol}{parseFloat(p.prices[0]?.amount).toFixed(2)}</p>
                                            <p className="spec-badges">
                                                <span>GSM: {p.gsm || 'N/A'}</span>
                                                {p.is_hypoallergenic && <span className="hypo-badge">Hypo</span>}
                                            </p>
                                        </div>
                                        <div className="product-actions">
                                            <button className="btn-edit" onClick={() => openEditForm(p)}>Edit</button>
                                            <button className="btn-delete" onClick={() => handleDeleteProduct(p.id)}>Delete</button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </aside>
            </div>

            {/* Inventory Form Modal */}
            {showAddForm && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h2>{editingProduct ? 'Edit Fabric Specifications' : 'List New Fabric Product'}</h2>
                        <form onSubmit={handleProductSubmit}>
                            <div className="form-group">
                                <label>Fabric Product Name</label>
                                <input 
                                    type="text" 
                                    required 
                                    placeholder="e.g. Organic Heavy Linen Weave" 
                                    value={pName} 
                                    onChange={(e) => setPName(e.target.value)} 
                                />
                            </div>

                            <div className="onboard-grid">
                                <div className="form-group">
                                    <label>Price per Meter ($)</label>
                                    <input 
                                        type="text" 
                                        required 
                                        placeholder="e.g. 18.50" 
                                        value={pPrice} 
                                        onChange={(e) => setPPrice(e.target.value)} 
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Stock Status</label>
                                    <select value={pInStock ? 'true' : 'false'} onChange={(e) => setPInStock(e.target.value === 'true')}>
                                        <option value="true">In Stock / Available</option>
                                        <option value="false">Out of Stock</option>
                                    </select>
                                </div>
                            </div>

                            <div className="form-group">
                                <label>Upload Local Image File</label>
                                <input 
                                    type="file" 
                                    accept="image/*" 
                                    onChange={handleFileUpload} 
                                    disabled={uploading}
                                />
                                {uploading && <p className="text-muted" style={{ fontSize: '0.85rem', marginTop: '4px' }}>Uploading image...</p>}
                            </div>

                            {pGallery.split('\n').filter(url => url.trim() !== '').length > 0 && (
                                <div className="form-group">
                                    <label>Gallery Preview</label>
                                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginTop: '6px' }}>
                                        {pGallery.split('\n').filter(url => url.trim() !== '').map((url, idx) => (
                                            <div key={idx} style={{ position: 'relative' }}>
                                                <img 
                                                    src={resolveImageUrl(url)}
                                                    alt={`preview-${idx}`} 
                                                    style={{ width: '64px', height: '64px', objectFit: 'cover', borderRadius: '4px', border: '1px solid #ccc' }} 
                                                />
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="form-group">
                                <label>Product Description</label>
                                <textarea 
                                    rows="3" 
                                    placeholder="Fabric composition, feel, applications..." 
                                    value={pDesc} 
                                    onChange={(e) => setPDesc(e.target.value)} 
                                />
                            </div>

                            <div className="divider"></div>
                            <h3>🌦 AI assistant Recommendation Metrics</h3>

                            <div className="onboard-grid">
                                <div className="form-group">
                                    <label>Fabric Weight (GSM)</label>
                                    <input 
                                        type="text" 
                                        placeholder="e.g. 150 (Grams/sq.m.)" 
                                        value={pGsm} 
                                        onChange={(e) => setPGsm(e.target.value)} 
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Breathability Rating (1-5)</label>
                                    <select value={pBreathability} onChange={(e) => setPBreathability(e.target.value)}>
                                        <option value="1">1 - Extremely low (Heavy coated fabrics)</option>
                                        <option value="2">2 - Low</option>
                                        <option value="3">3 - Moderate (Standard weave)</option>
                                        <option value="4">4 - High</option>
                                        <option value="5">5 - Maximum (Open Linen, Cotton Poplin)</option>
                                    </select>
                                </div>
                            </div>

                            <div className="onboard-grid">
                                <div className="form-group">
                                    <label>Texture Smoothness (1-5)</label>
                                    <select value={pSmoothness} onChange={(e) => setPSmoothness(e.target.value)}>
                                        <option value="1">1 - Very rough / scratchy (Raw wool)</option>
                                        <option value="2">2 - Structured</option>
                                        <option value="3">3 - Standard Softness</option>
                                        <option value="4">4 - High Softness</option>
                                        <option value="5">5 - Silky / Extremely Smooth (Silk, Bamboo)</option>
                                    </select>
                                </div>
                            </div>

                            <div className="checkboxes-flex">
                                <label className="checkbox-label">
                                    <input 
                                        type="checkbox" 
                                        checked={pHypoallergenic} 
                                        onChange={(e) => setPHypoallergenic(e.target.checked)} 
                                    />
                                    <span>Hypoallergenic Fabric (Safe for sensitive skin)</span>
                                </label>
                                <label className="checkbox-label">
                                    <input 
                                        type="checkbox" 
                                        checked={pOekoTex} 
                                        onChange={(e) => setPOekoTex(e.target.checked)} 
                                    />
                                    <span>OEKO-TEX® Standard 100 Certified (Chemical-free)</span>
                                </label>
                            </div>

                            <div className="form-group">
                                <label>Recommended Climates</label>
                                <div className="climates-flex">
                                    {['Tropical', 'Temperate', 'Polar'].map((c) => (
                                        <button
                                            type="button"
                                            key={c}
                                            className={`climate-pill ${pClimates.includes(c) ? 'selected' : ''}`}
                                            onClick={() => toggleClimateSelection(c)}
                                        >
                                            {c}
                                        </button>
                                    ))}
                                </div>
                            </div>

                            <div className="button-group">
                                <button type="submit" className="btn-primary">Save Product</button>
                                <button type="button" className="btn-secondary" onClick={() => { setShowAddForm(false); setEditingProduct(null); }}>
                                    Cancel
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
