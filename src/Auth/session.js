/**
 * Auth session storage.
 *
 * Auth state deliberately lives outside Redux (in localStorage), so that a
 * page reload keeps you logged in without rehydrating the whole store. This
 * module is the only place that should touch those keys — components used to
 * call localStorage.getItem('token') directly in 14 places.
 *
 * Note clearSession() removes only the auth keys. The previous code called
 * localStorage.clear(), which also wiped the redux-persist store under
 * `ankh-store-v2` and forced a hard page navigation to recover.
 */

const TOKEN_KEY = 'token';
const ROLE_KEY = 'role';
const USER_KEY = 'user';

export const getToken = () => localStorage.getItem(TOKEN_KEY);

export const getRole = () => localStorage.getItem(ROLE_KEY);

export const getUser = () => {
    const raw = localStorage.getItem(USER_KEY);
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch (e) {
        // A corrupt entry should log you out cleanly rather than crash render.
        console.error('Stored user profile is not valid JSON; clearing it.', e);
        localStorage.removeItem(USER_KEY);
        return null;
    }
};

export const isLoggedIn = () => Boolean(getToken());

/** Persist the token + role returned by POST /api/auth/login. */
export const setSession = ({ token, role }) => {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    if (role) localStorage.setItem(ROLE_KEY, role);
};

/** Persist the profile returned by GET /api/auth/me. */
export const setUser = (user) => {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
};

/** Remove only the auth keys, leaving the persisted Redux store intact. */
export const clearSession = () => {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(ROLE_KEY);
    localStorage.removeItem(USER_KEY);
};

/** Authorization header, or {} when not logged in. */
export const authHeader = () => {
    const token = getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
};
