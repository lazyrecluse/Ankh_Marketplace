/**
 * User-Scoped Cart Storage.
 *
 * Ensures shopping carts are unique to each user session and account.
 * - Guests have their cart stored under 'ankh_cart_guest'.
 * - Logged-in users have their cart stored under 'ankh_cart_user_<id>'.
 * - When a guest logs in or registers, their guest cart is migrated to their account.
 * - When a user logs out, their cart is saved to their user key and Redux is reset,
 *   preventing one account's cart from leaking into another account.
 */

const GUEST_CART_KEY = 'ankh_cart_guest';

export const getCartStorageKey = (userId) => {
    return userId ? `ankh_cart_user_${userId}` : GUEST_CART_KEY;
};

export const loadCartFromStorage = (userId) => {
    try {
        const key = getCartStorageKey(userId);
        const raw = localStorage.getItem(key);
        return raw ? JSON.parse(raw) : [];
    } catch (e) {
        console.error('Failed to load cart from storage:', e);
        return [];
    }
};

export const saveCartToStorage = (userId, cartItems) => {
    try {
        const key = getCartStorageKey(userId);
        localStorage.setItem(key, JSON.stringify(cartItems || []));
    } catch (e) {
        console.error('Failed to save cart to storage:', e);
    }
};

export const clearGuestCart = () => {
    try {
        localStorage.removeItem(GUEST_CART_KEY);
    } catch (e) {
        console.error('Failed to clear guest cart:', e);
    }
};

/**
 * Merge two carts. If an item matches by id and attributes, increment quantity.
 */
export const mergeCarts = (baseCart = [], incomingCart = []) => {
    const result = [...baseCart];

    for (const item of incomingCart) {
        // Look for matching product
        const matchIndex = result.findIndex((existing) => {
            if (existing.id !== item.id) return false;
            // Compare attribute keys
            const existingAttrs = existing.attributes || [];
            return existingAttrs.every((attr) => existing[attr.name] === item[attr.name]);
        });

        if (matchIndex >= 0) {
            const currentQty = parseInt(result[matchIndex].quantity) || 1;
            const addQty = parseInt(item.quantity) || 1;
            result[matchIndex] = {
                ...result[matchIndex],
                quantity: currentQty + addQty,
            };
        } else {
            result.push(item);
        }
    }

    return result;
};
