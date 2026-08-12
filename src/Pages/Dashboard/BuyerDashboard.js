import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useHistory } from 'react-router-dom';
import { getProducts } from '../../Api/catalog';
import { getMe } from '../../Api/auth';
import { getBuyerOrders } from '../../Api/orders';
import * as session from '../../Auth/session';
import { resolveImageUrl } from '../../Api/client';
import './Dashboard.scss';

export default function BuyerDashboard() {
    const history = useHistory();
    const [orders, setOrders] = useState([]);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    // Search and filter states
    const [products, setProducts] = useState([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [categoryFilter, setCategoryFilter] = useState('All');
    const [climateFilter, setClimateFilter] = useState('All');
    const [sensitiveSkinFilter, setSensitiveSkinFilter] = useState(false);
    const [priceFilter, setPriceFilter] = useState('');

    // Held in a ref rather than closed over, so that fetchProducts stays stable
    // as the shopper types. Closing over searchQuery would make fetchProducts a
    // new function per keystroke, and the effect below would then fire a
    // request per keystroke.
    const searchQueryRef = useRef(searchQuery);
    useEffect(() => {
        searchQueryRef.current = searchQuery;
    }, [searchQuery]);

    const fetchProducts = useCallback(async () => {
        try {
            let data = await getProducts({
                category: categoryFilter !== 'All' ? categoryFilter : null,
                search: searchQueryRef.current || null,
                climate: climateFilter !== 'All' ? climateFilter : null,
                sensitive_skin: sensitiveSkinFilter || null
            });

            // Client side filter for max price if specified
            if (priceFilter) {
                const maxP = parseFloat(priceFilter);
                if (!isNaN(maxP)) {
                    data = data.filter(p => {
                        const price = p.prices?.[0]?.amount || 0;
                        return price <= maxP;
                    });
                }
            }
            setProducts(data);
        } catch (err) {
            console.error('Failed to load products:', err);
        }
    }, [categoryFilter, climateFilter, sensitiveSkinFilter, priceFilter]);

    useEffect(() => {
        fetchProducts();
    }, [fetchProducts]);

    useEffect(() => {
        if (!session.isLoggedIn()) {
            history.push('/login');
            return;
        }

        const fetchBuyerData = async () => {
            try {
                setUser(await getMe());
                setOrders(await getBuyerOrders());
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchBuyerData();
    }, [history]);

    const handleSearchSubmit = (e) => {
        if (e) e.preventDefault();
        fetchProducts();
    };

    const handleLogout = () => {
        session.clearSession();
        window.location.href = '/login';
    };

    if (loading) return <div className="dashboard-loading">Loading Buyer Dashboard...</div>;

    return (
        <div className="dashboard-container">
            <header className="dashboard-header">
                <div>
                    <h1>Buyer Dashboard</h1>
                    <p className="welcome">Logged in as: <strong>{user?.email}</strong></p>
                </div>
                <div className="header-actions">
                    <button className="btn-secondary" onClick={() => history.push('/products')}>Browse Fabrics</button>
                    <button className="btn-logout" onClick={handleLogout}>Log Out</button>
                </div>
            </header>

            {error && <div className="dashboard-alert error">{error}</div>}

            <div className="dashboard-layout">
                {/* Profile Card */}
                <aside className="dashboard-sidebar">
                    <div className="card profile-card">
                        <h3>Business Profile</h3>
                        <div className="profile-detail">
                            <span className="label">Business Type:</span>
                            <span className="value">{user?.profile?.business_type || 'Not Set'}</span>
                        </div>
                        <div className="profile-detail">
                            <span className="label">Primary Industry:</span>
                            <span className="value">{user?.profile?.industry || 'Not Set'}</span>
                        </div>
                        <div className="profile-detail">
                            <span className="label">Typical Order Qty:</span>
                            <span className="value">{user?.profile?.typical_order_qty || 'Not Set'}</span>
                        </div>
                        <div className="profile-detail">
                            <span className="label">Budget Range:</span>
                            <span className="value">{user?.profile?.budget_range || 'Not Set'}</span>
                        </div>

                        <div className="divider"></div>

                        <h3>🌦 AI Recommendation Settings</h3>
                        <div className="profile-detail">
                            <span className="label">Target Climate:</span>
                            <span className="value highlight-badge">{user?.profile?.preferred_climate || 'All'}</span>
                        </div>
                        <div className="profile-detail">
                            <span className="label">Skin Sensitivity:</span>
                            <span className={`value ${user?.profile?.has_sensitive_skin ? 'text-alert' : ''}`}>
                                {user?.profile?.has_sensitive_skin ? '⚠️ Sensitive Skin Mode' : 'Standard'}
                            </span>
                        </div>
                        {user?.profile?.has_sensitive_skin && (
                            <div className="profile-detail flex-col">
                                <span className="label">Requirements:</span>
                                <div className="tags-list">
                                    {user?.profile?.skin_preferences?.map((tag, i) => (
                                        <span key={i} className="small-tag">{tag}</span>
                                    ))}
                                </div>
                            </div>
                        )}
                        <button className="btn-edit-profile" onClick={() => history.push('/onboarding/buyer')}>
                            Edit Preferences
                        </button>
                    </div>
                </aside>

                {/* Orders List */}
                <main className="dashboard-content">
                    {/* Search and Filters panel */}
                    <div className="card catalog-search-card">
                        <h3>🔍 Traditional Fabric Search & Filters</h3>
                        <form onSubmit={handleSearchSubmit} className="search-filter-form">
                            <div className="search-row">
                                <input 
                                    type="text" 
                                    placeholder="Search by fabric name, brand, or specs..." 
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    className="search-input"
                                />
                                <button type="submit" className="btn-search">Search</button>
                            </div>
                            <div className="filters-row">
                                <div className="filter-group">
                                    <label>Category</label>
                                    <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
                                        <option value="All">All Categories</option>
                                        <option value="Cotton">Cotton</option>
                                        <option value="Silk">Silk</option>
                                        <option value="Linen">Linen</option>
                                        <option value="Woolen">Woolen</option>
                                        <option value="Mohair">Mohair</option>
                                        <option value="Ankara">Ankara</option>
                                        <option value="Kente">Kente</option>
                                        <option value="Velvet">Velvet</option>
                                        <option value="Cashmere">Cashmere</option>
                                    </select>
                                </div>
                                <div className="filter-group">
                                    <label>Climate</label>
                                    <select value={climateFilter} onChange={(e) => setClimateFilter(e.target.value)}>
                                        <option value="All">All Climates</option>
                                        <option value="Tropical">Tropical</option>
                                        <option value="Temperate">Temperate</option>
                                        <option value="Polar">Polar</option>
                                    </select>
                                </div>
                                <div className="filter-group">
                                    <label>Max Price ($)</label>
                                    <input 
                                        type="number" 
                                        placeholder="e.g. 50" 
                                        value={priceFilter}
                                        onChange={(e) => setPriceFilter(e.target.value)}
                                        className="price-input"
                                        min="0"
                                        step="0.01"
                                    />
                                </div>
                                <div className="filter-group checkbox-group">
                                    <label className="checkbox-label">
                                        <input 
                                            type="checkbox" 
                                            checked={sensitiveSkinFilter} 
                                            onChange={(e) => setSensitiveSkinFilter(e.target.checked)}
                                        />
                                        <span>Hypoallergenic</span>
                                    </label>
                                </div>
                                <button 
                                    type="button" 
                                    className="btn-clear-filters"
                                    onClick={() => {
                                        setSearchQuery('');
                                        setCategoryFilter('All');
                                        setClimateFilter('All');
                                        setPriceFilter('');
                                        setSensitiveSkinFilter(false);
                                    }}
                                >
                                    Reset
                                </button>
                            </div>
                        </form>
                    </div>

                    <div className="card catalog-results-card">
                        <h3>Fabric Catalog ({products.length})</h3>
                        {products.length === 0 ? (
                            <div className="empty-state">No fabrics match your search criteria.</div>
                        ) : (
                            <div className="buyer-products-grid">
                                {products.map((p) => (
                                    <div key={p.id} className="buyer-product-card" onClick={() => history.push(`/products/${p.id}`)}>
                                        <img 
                                            src={resolveImageUrl(p.gallery?.[0], 'https://via.placeholder.com/150')}
                                            alt={p.name} 
                                        />
                                        <div className="p-info">
                                            <span className="brand-tag">{p.brand}</span>
                                            <h4>{p.name}</h4>
                                            <p className="description">{p.description ? (p.description.substring(0, 80) + '...') : ''}</p>
                                            <div className="footer-meta">
                                                <span className="price">{p.prices && p.prices[0]?.currency?.symbol}{p.prices && parseFloat(p.prices[0]?.amount).toFixed(2)}/m</span>
                                                <span className={`stock-status ${p.inStock ? 'in-stock' : 'out-of-stock'}`}>
                                                    {p.inStock ? 'Available' : 'Out of Stock'}
                                                </span>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>

                    <div className="card orders-card">
                        <h3>Order History ({orders.length})</h3>
                        {orders.length === 0 ? (
                            <div className="empty-state">
                                <p>You haven't placed any B2B fabric orders yet.</p>
                                <button className="btn-primary-sm" onClick={() => history.push('/products')}>
                                    Start Browsing Fabrics
                                </button>
                            </div>
                        ) : (
                            <div className="orders-table-wrapper">
                                <table className="orders-table">
                                    <thead>
                                        <tr>
                                            <th>Order ID</th>
                                            <th>Date</th>
                                            <th>Recipient</th>
                                            <th>Fabrics Ordered</th>
                                            <th>Total Price</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {orders.map((o) => (
                                            <tr key={o.id}>
                                                <td><strong>#{o.id}</strong></td>
                                                <td>{new Date(o.created_at).toLocaleDateString()}</td>
                                                <td>
                                                    <div className="recipient-info">
                                                        <span>{o.shipping_name}</span>
                                                        <small className="text-muted">{o.shipping_address}</small>
                                                    </div>
                                                </td>
                                                <td>
                                                    <ul className="items-list">
                                                        {o.items.map((item, idx) => (
                                                            <li key={idx}>
                                                                {item.product_name} ({item.quantity} units)
                                                            </li>
                                                        ))}
                                                    </ul>
                                                </td>
                                                <td className="price-col">{o.currency_symbol}{parseFloat(o.total_price).toFixed(2)}</td>
                                                <td>
                                                    <span className={`status-badge ${o.status.toLowerCase().replace(/\s+/g, '-')}`}>
                                                        {o.status}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </div>
                </main>
            </div>
        </div>
    );
}
