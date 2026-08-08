import { get, post } from './client';

export const placeOrder = (order) => post('/api/orders', order, { auth: true });

export const getBuyerOrders = () => get('/api/buyer/orders', { auth: true });
