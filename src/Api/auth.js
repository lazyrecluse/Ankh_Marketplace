import { get, post } from './client';

export const login = (email, password) =>
    post('/api/auth/login', { email, password });

export const register = (email, password, role) =>
    post('/api/auth/register', { email, password, role });

/** Current user + profile. Used after login and on dashboard mount. */
export const getMe = () => get('/api/auth/me', { auth: true });
