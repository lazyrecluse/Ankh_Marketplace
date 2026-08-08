import React, { useState } from 'react';
import { useHistory, useLocation, Link } from 'react-router-dom';
import './AuthPage.scss';
import * as authApi from '../../Api/auth';
import * as session from '../../Auth/session';

export default function AuthPage({ buyerMode = false }) {
    const history = useHistory();
    const location = useLocation();
    const isBuyerMode = buyerMode || (location && location.pathname === '/login/buyer');
    const [isLogin, setIsLogin] = useState(true);
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState('buyer');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            if (isLogin) {
                const data = await authApi.login(email, password);
                session.setSession({ token: data.access_token, role: data.role });

                // Fetch profile to check if onboarding is completed
                const meData = await authApi.getMe();
                session.setUser(meData);

                // Route based on role and onboarding state
                if (data.role === 'buyer') {
                    const needsOnboarding = !meData.profile || !meData.profile.business_type;
                    history.push(needsOnboarding ? '/onboarding/buyer' : '/products');
                } else {
                    const needsOnboarding = !meData.profile || !meData.profile.business_name;
                    history.push(needsOnboarding ? '/onboarding/supplier' : '/supplier/dashboard');
                }
            } else {
                await authApi.register(email, password, role);
                setIsLogin(true);
                setError('Registration successful! Please log in.');
            }
        } catch (err) {
            setError(err.message || 'An error occurred');
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
