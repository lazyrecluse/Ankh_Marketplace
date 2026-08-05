import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import { back_end_endpoint } from '../../Configs/BackEndEndpoint';
import './Onboarding.scss';

export default function BuyerOnboarding() {
    const history = useHistory();
    const [businessType, setBusinessType] = useState('');
    const [industry, setIndustry] = useState('');
    const [orderQty, setOrderQty] = useState('');
    const [budget, setBudget] = useState('');
    
    // Climate & Skin Preferences for AI recommendation
    const [climate, setClimate] = useState('All');
    const [sensitiveSkin, setSensitiveSkin] = useState(false);
    const [skinPrefs, setSkinPrefs] = useState([]);
    
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const toggleSkinPreference = (tag) => {
        if (skinPrefs.includes(tag)) {
            setSkinPrefs(skinPrefs.filter(t => t !== tag));
        } else {
            setSkinPrefs([...skinPrefs, tag]);
        }
    };

    const handleOnboard = async (e, isSkip = false) => {
        if (e) e.preventDefault();
        setError('');
        setLoading(true);

        const token = localStorage.getItem('token');
        if (!token) {
            history.push('/login');
            return;
        }

        const body = isSkip ? {
            business_type: 'Not Specified',
            industry: 'Not Specified',
            typical_order_qty: '0',
            budget_range: 'Not Specified',
            preferred_climate: 'All',
            has_sensitive_skin: false,
            skin_preferences: []
        } : {
            business_type: businessType,
            industry: industry,
            typical_order_qty: orderQty,
            budget_range: budget,
            preferred_climate: climate,
            has_sensitive_skin: sensitiveSkin,
            skin_preferences: skinPrefs
        };

        try {
            const res = await fetch(back_end_endpoint() + '/api/onboarding/buyer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(body)
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.detail || 'Failed to submit onboarding');
            }

            // Fetch updated profile
            const meRes = await fetch(back_end_endpoint() + '/api/auth/me', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            const meData = await meRes.json();
            localStorage.setItem('user', JSON.stringify(meData));

            // Redirect to home discovery
            history.push('/products');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="onboard-container">
            <div className="onboard-card">
                <h2>Configure Your Buyer Profile</h2>
                <p className="subtitle">Let us customize your textile discovery experience. You can update these settings anytime.</p>

                {error && <div className="onboard-alert error">{error}</div>}

                <form onSubmit={(e) => handleOnboard(e, false)}>
                    <div className="onboard-grid">
                        <div className="form-group">
                            <label>Business Type</label>
                            <select value={businessType} onChange={(e) => setBusinessType(e.target.value)} required>
                                <option value="">Select Type...</option>
                                <option value="Brand / Label">Brand / Label</option>
                                <option value="Retailer">Retailer</option>
                                <option value="Manufacturer">Manufacturer</option>
                                <option value="Wholesaler">Wholesaler</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label>Primary Industry</label>
                            <select value={industry} onChange={(e) => setIndustry(e.target.value)} required>
                                <option value="">Select Industry...</option>
                                <option value="Apparel / Fashion">Apparel / Fashion</option>
                                <option value="Home Furnishings">Home Furnishings</option>
                                <option value="Technical Textiles">Technical Textiles</option>
                                <option value="Industrial Design">Industrial Design</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label>Typical Order Volume</label>
                            <input 
                                type="text" 
                                placeholder="e.g. 500 meters, 10 rolls" 
                                value={orderQty} 
                                onChange={(e) => setOrderQty(e.target.value)} 
                                required
                            />
                        </div>

                        <div className="form-group">
                            <label>Budget Range</label>
                            <select value={budget} onChange={(e) => setBudget(e.target.value)} required>
                                <option value="">Select Range...</option>
                                <option value="Economy ($ - $$)">Economy ($ - $$)</option>
                                <option value="Premium ($$ - $$$)">Premium ($$ - $$$)</option>
                                <option value="Luxury ($$$+)">Luxury ($$$+)</option>
                            </select>
                        </div>
                    </div>

                    <div className="divider"></div>

                    <h3>🌦 Climate & Fabric Preferences (AI-Enabled)</h3>
                    <p className="section-sub">We use these options to filter fabrics by breathability, GSM, and weave structure.</p>

                    <div className="form-group">
                        <label>Target Climate Profile</label>
                        <div className="climate-selector">
                            {['All', 'Tropical', 'Temperate', 'Polar'].map((c) => (
                                <button 
                                    type="button" 
                                    key={c}
                                    className={`climate-btn ${climate === c ? 'active' : ''}`}
                                    onClick={() => setClimate(c)}
                                >
                                    {c === 'All' && '🌍 All/Any'}
                                    {c === 'Tropical' && '☀️ Tropical/Humid'}
                                    {c === 'Temperate' && '🍃 Temperate/Mild'}
                                    {c === 'Polar' && '❄️ Cold/Polar'}
                                </button>
                            ))}
                        </div>
                    </div>

                    <div className="form-group checkbox-group">
                        <label className="checkbox-label">
                            <input 
                                type="checkbox" 
                                checked={sensitiveSkin} 
                                onChange={(e) => setSensitiveSkin(e.target.checked)} 
                            />
                            <span>My clients or products require sensitive-skin fabrics</span>
                        </label>
                    </div>

                    {sensitiveSkin && (
                        <div className="form-group">
                            <label>Specific Skin Requirements</label>
                            <div className="tags-container">
                                {['Hypoallergenic Only', 'Organic Certified', 'Ultra Soft Textures Only', 'OEKO-TEX Certified Only'].map((tag) => (
                                    <button
                                        type="button"
                                        key={tag}
                                        className={`tag-btn ${skinPrefs.includes(tag) ? 'selected' : ''}`}
                                        onClick={() => toggleSkinPreference(tag)}
                                    >
                                        {tag}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    <div className="button-group">
                        <button type="submit" className="btn-primary" disabled={loading}>
                            {loading ? 'Submitting...' : 'Complete Profile'}
                        </button>
                        <button type="button" className="btn-secondary" onClick={() => handleOnboard(null, true)} disabled={loading}>
                            Skip for Now
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
}
