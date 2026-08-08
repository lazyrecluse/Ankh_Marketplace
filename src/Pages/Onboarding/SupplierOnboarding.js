import React, { useState } from 'react';
import { useHistory } from 'react-router-dom';
import './Onboarding.scss';
import * as onboardingApi from '../../Api/onboarding';
import * as authApi from '../../Api/auth';
import * as session from '../../Auth/session';

export default function SupplierOnboarding() {
    const history = useHistory();
    const [businessName, setBusinessName] = useState('');
    const [businessType, setBusinessType] = useState('');
    const [contactInfo, setContactInfo] = useState('');
    const [address, setAddress] = useState('');
    const [operatingHours, setOperatingHours] = useState('');
    const [selectedCats, setSelectedCats] = useState([]);
    
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const toggleCategory = (cat) => {
        if (selectedCats.includes(cat)) {
            setSelectedCats(selectedCats.filter(c => c !== cat));
        } else {
            setSelectedCats([...selectedCats, cat]);
        }
    };

    const handleOnboard = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        if (!session.isLoggedIn()) {
            history.push('/login');
            return;
        }

        try {
            await onboardingApi.submitSupplierOnboarding({
                business_name: businessName,
                business_type: businessType,
                contact_info: contactInfo,
                address: address,
                operating_hours: operatingHours,
                categories: selectedCats
            });

            const meData = await authApi.getMe();
            session.setUser(meData);

            history.push('/supplier/dashboard');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="onboard-container">
            <div className="onboard-card">
                <h2>Configure Your Supplier Profile</h2>
                <p className="subtitle">Set up your business presence to start listing your fabric collections to B2B buyers.</p>

                {error && <div className="onboard-alert error">{error}</div>}

                <form onSubmit={handleOnboard}>
                    <div className="form-group">
                        <label>Business / Company Name</label>
                        <input 
                            type="text" 
                            required 
                            placeholder="e.g. Nile Valley Weavers Ltd" 
                            value={businessName} 
                            onChange={(e) => setBusinessName(e.target.value)} 
                        />
                    </div>

                    <div className="onboard-grid">
                        <div className="form-group">
                            <label>Facility Type</label>
                            <select value={businessType} onChange={(e) => setBusinessType(e.target.value)} required>
                                <option value="">Select Type...</option>
                                <option value="Integrated Mill">Integrated Mill</option>
                                <option value="Weaving House">Weaving House</option>
                                <option value="Knitting Facility">Knitting Facility</option>
                                <option value="Spinning Mill">Spinning Mill</option>
                                <option value="Dyeing & Finishing">Dyeing & Finishing</option>
                            </select>
                        </div>

                        <div className="form-group">
                            <label>Contact Phone / Email</label>
                            <input 
                                type="text" 
                                required 
                                placeholder="e.g. sales@nileweavers.com" 
                                value={contactInfo} 
                                onChange={(e) => setContactInfo(e.target.value)} 
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label>Operating Hours</label>
                        <input 
                            type="text" 
                            required 
                            placeholder="e.g. Mon-Fri 08:00 - 17:00 EET" 
                            value={operatingHours} 
                            onChange={(e) => setOperatingHours(e.target.value)} 
                        />
                    </div>

                    <div className="form-group">
                        <label>Warehouse / Business Address</label>
                        <textarea 
                            rows="2"
                            required 
                            placeholder="Full address of your primary shipping facility..." 
                            value={address} 
                            onChange={(e) => setAddress(e.target.value)} 
                        />
                    </div>

                    <div className="form-group">
                        <label>Fabric Categories You Offer</label>
                        <div className="tags-container">
                            {['cotton', 'silk', 'linen', 'woolen', 'mohair', 'ankara', 'kente', 'velvet', 'cashmere'].map((cat) => (
                                <button
                                    type="button"
                                    key={cat}
                                    className={`tag-btn ${selectedCats.includes(cat) ? 'selected' : ''}`}
                                    onClick={() => toggleCategory(cat)}
                                >
                                    {cat.toUpperCase()}
                                </button>
                            ))}
                        </div>
                    </div>

                    <button type="submit" className="btn-primary" disabled={loading}>
                        {loading ? 'Submitting...' : 'Register Business & Go to Dashboard'}
                    </button>
                </form>
            </div>
        </div>
    );
}
