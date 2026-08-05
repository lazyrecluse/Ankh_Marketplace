import React, { useState, useEffect } from 'react';
import { useHistory } from 'react-router-dom';
import { back_end_endpoint } from '../../Configs/BackEndEndpoint';
import './Dashboard.scss';

export default function BuyerDashboard() {
    const history = useHistory();
    const [orders, setOrders] = useState([]);
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            history.push('/login');
            return;
        }

        const fetchBuyerData = async () => {
            try {
                // Get profile
                const meRes = await fetch(back_end_endpoint() + '/api/auth/me', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!meRes.ok) throw new Error('Failed to fetch profile details');
                const meData = await meRes.json();
                setUser(meData);

                // Get orders
                const ordersRes = await fetch(back_end_endpoint() + '/api/buyer/orders', {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!ordersRes.ok) throw new Error('Failed to fetch order history');
                const ordersData = await ordersRes.json();
                setOrders(ordersData);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }
        };

        fetchBuyerData();
    }, [history]);

    const handleLogout = () => {
        localStorage.clear();
        history.push('/login');
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
