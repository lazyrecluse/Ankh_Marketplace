import React, { useState } from 'react';
import { useHistory, useLocation, Link } from 'react-router-dom';
import { back_end_endpoint } from '../../Configs/BackEndEndpoint';
import './AuthPage.scss';

export default function AuthPage({ buyerMode = false }) {
    const history = useHistory();
    const location = useLocation();
    const isBuyerMode = buyerMode || (location && location.pathname === '/login/buyer');
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('buyer'); // buyer or supplier
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        const endpoint = isLogin ? '/api/auth/login' : '/api/auth/register';
        const body = isLogin 
            ? { email, password } 
            : { email, password, role };

        try {
            const res = await fetch(back_end_endpoint() + endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            const data = await res.json();
            if (!res.ok) {
                throw new Error(data.detail || 'Authentication failed');
            }

            if (isLogin) {
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('role', data.role);
                
                // Fetch profile to verify if onboarding is completed
                const meRes = await fetch(back_end_endpoint() + '/api/auth/me', {
                    headers: { 'Authorization': `Bearer ${data.access_token}` }
                });
                const meData = await meRes.json();
                localStorage.setItem('user', JSON.stringify(meData));

                // Route accordingly
                if (data.role === 'buyer') {
                    if (meData.profile && meData.profile.business_type) {
                        history.push('/products');
                    } else {
                        history.push('/onboarding/buyer');
                    }
                } else {
                    if (meData.profile && meData.profile.business_name) {
                        history.push('/supplier/dashboard');
                    } else {
                        history.push('/onboarding/supplier');
                    }
                }
            } else {
                // After successful registration, toggle to login screen
                setIsLogin(true);
                setError('Registration successful! Please login.');
            }
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="auth-container">
            <div className="auth-card">
                {isBuyerMode && <div className="buyer-badge">Buyer Mode</div>}
                <h2>{isLogin ? (isBuyerMode ? 'Buyer Sign In' : 'Welcome Back') : 'Join Ankh Marketplace'}</h2>
                <p className="subtitle">{isLogin ? (isBuyerMode ? 'Sign in to your buyer account to discover & order textiles' : 'Sign in to discover premium textiles') : 'Register to trade high-quality fabrics'}</p>
                
                {error && <div className={`auth-alert ${error.includes('successful') ? 'success' : 'error'}`}>{error}</div>}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Business Email</label>
                        <input 
                            type="email" 
                            required 
                            placeholder="you@company.com" 
                            value={email} 
                            onChange={(e) => setEmail(e.target.value)} 
                        />
                    </div>
                    <div className="form-group">
                        <label>Password</label>
                        <input 
                            type="password" 
                            required 
                            placeholder="••••••••" 
                            value={password} 
                            onChange={(e) => setPassword(e.target.value)} 
                        />
                    </div>
                    
                    {!isLogin && (
                        <div className="form-group">
                            <label>I want to join as a</label>
                            <div className="role-selector">
                                <label className={role === 'buyer' ? 'active' : ''}>
                                    <input 
                                        type="radio" 
                                        name="role" 
                                        value="buyer" 
                                        checked={role === 'buyer'}
                                        onChange={() => setRole('buyer')}
                                    />
                                    Buyer / Retailer
                                </label>
                                <label className={role === 'supplier' ? 'active' : ''}>
                                    <input 
                                        type="radio" 
                                        name="role" 
                                        value="supplier" 
                                        checked={role === 'supplier'}
                                        onChange={() => setRole('supplier')}
                                    />
                                    Supplier / Weaver
                                </label>
                            </div>
                        </div>
                    )}

                    <button type="submit" className="btn-primary" disabled={loading}>
                        {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Create Account')}
                    </button>
                </form>

                {isLogin && (
                    <div className="auth-helper-link">
                        {isBuyerMode ? (
                            <p>
                                <Link to="/login" className="auth-helper-link">Supplier / Standard sign in</Link>
                            </p>
                        ) : (
                            <p>
                                Are you a buyer? <Link to="/login/buyer" className="auth-helper-link">Sign in here</Link>
                            </p>
                        )}
                    </div>
                )}

                <div className="auth-toggle">
                    <p>
                        {isLogin ? "Don't have an account?" : "Already have an account?"}
                        <button type="button" onClick={() => setIsLogin(!isLogin)}>
                            {isLogin ? 'Create one now' : 'Sign In instead'}
                        </button>
                    </p>
                </div>
            </div>
        </div>
    );
}
