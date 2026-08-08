import { get } from './client';

export const getCategories = () => get('/api/categories');

export const getCurrencies = () => get('/api/currencies');

/**
 * @param {object} [filters]
 * @param {string} [filters.category]
 * @param {string} [filters.search]
 * @param {string} [filters.climate]
 * @param {boolean} [filters.sensitive_skin]
 * @param {number} [filters.supplier_id]
 */
export const getProducts = (filters = {}) =>
    get('/api/products', { params: filters });

export const getProduct = (productId) => get(`/api/products/${productId}`);
