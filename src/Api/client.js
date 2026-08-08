/**
 * HTTP client for the FastAPI backend.
 *
 * Replaces 23 hand-rolled `fetch(back_end_endpoint() + path, {...})` calls
 * that each rebuilt the base URL, the Authorization header, and their own
 * res.ok / error-detail handling.
 *
 * Errors are thrown as ApiError so callers keep working with the
 * `catch (err) { setError(err.message) }` pattern already used across the app,
 * but can now also branch on err.status when they need to.
 */

import { back_end_endpoint } from '../Configs/BackEndEndpoint';
import { authHeader } from '../Auth/session';

export class ApiError extends Error {
    constructor(message, status, detail) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
        this.detail = detail;
    }
}

/**
 * @param {string} path      Path beginning with '/', e.g. '/api/products'
 * @param {object} [options]
 * @param {string} [options.method='GET']
 * @param {object} [options.body]    Serialized as JSON unless it is FormData
 * @param {boolean} [options.auth=false]  Send the bearer token
 * @param {object} [options.params] Query string values; null/undefined skipped
 */
export const request = async (path, options = {}) => {
    const { method = 'GET', body, auth = false, params } = options;

    let url = back_end_endpoint() + path;

    if (params) {
        const search = new URLSearchParams();
        Object.entries(params).forEach(([key, value]) => {
            if (value !== null && value !== undefined && value !== '') {
                search.append(key, value);
            }
        });
        const qs = search.toString();
        if (qs) url += `?${qs}`;
    }

    const isFormData = typeof FormData !== 'undefined' && body instanceof FormData;

    const headers = {
        // FormData must NOT get an explicit Content-Type — the browser has to
        // set it so the multipart boundary is included.
        ...(isFormData || body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...(auth ? authHeader() : {}),
    };

    let response;
    try {
        response = await fetch(url, {
            method,
            headers,
            ...(body === undefined ? {} : { body: isFormData ? body : JSON.stringify(body) }),
        });
    } catch (networkError) {
        // fetch only rejects on network failure, never on a 4xx/5xx.
        throw new ApiError(
            'Could not reach the server. Is the backend running?',
            0,
            networkError.message
        );
    }

    // 204 and other empty bodies would blow up res.json().
    const text = await response.text();
    let payload = null;
    if (text) {
        try {
            payload = JSON.parse(text);
        } catch (e) {
            payload = text;
        }
    }

    if (!response.ok) {
        const detail =
            payload && typeof payload === 'object' ? payload.detail : payload;
        throw new ApiError(
            detail || `Request failed with status ${response.status}`,
            response.status,
            detail
        );
    }

    return payload;
};

export const get = (path, options) => request(path, { ...options, method: 'GET' });
export const post = (path, body, options) =>
    request(path, { ...options, method: 'POST', body });
export const put = (path, body, options) =>
    request(path, { ...options, method: 'PUT', body });
export const del = (path, options) => request(path, { ...options, method: 'DELETE' });

/**
 * Resolve a gallery image URL for use in an <img src>.
 *
 * Uploaded images are stored as backend-relative paths ('/static/uploads/x.jpg')
 * while seeded ones are absolute Unsplash URLs, so every consumer needs this
 * check. It was copy-pasted at five call sites before this.
 */
export const resolveImageUrl = (url, fallback = null) => {
    if (!url) return fallback;
    return url.startsWith('/') ? back_end_endpoint() + url : url;
};
