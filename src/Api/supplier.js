import { del, get, post, put, request } from './client';

export const getDashboard = () => get('/api/supplier/dashboard', { auth: true });

export const getSupplierOrders = () => get('/api/supplier/orders', { auth: true });

export const updateOrderStatus = (orderId, status) =>
    put(`/api/supplier/orders/${orderId}/status`, { status }, { auth: true });

export const createProduct = (product) =>
    post('/api/supplier/products', product, { auth: true });

export const updateProduct = (productId, product) =>
    put(`/api/supplier/products/${productId}`, product, { auth: true });

export const deleteProduct = (productId) =>
    del(`/api/supplier/products/${productId}`, { auth: true });

/**
 * Upload a gallery image.
 * Returns the backend-relative URL, e.g. '/static/uploads/<uuid>.jpg'.
 */
export const uploadImage = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const data = await request('/api/upload', {
        method: 'POST',
        body: formData,
        auth: true,
    });
    return data.url || data.image_url;
};
