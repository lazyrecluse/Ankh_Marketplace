/**
 * Shared parsing/serializing for the product catalog's filter state.
 *
 * The filters live in the URL query string (`/products?search=silk&sort=price_asc`)
 * rather than in Redux, for three reasons:
 *
 *   - the Redux store is persisted to localStorage by redux-persist, so a search
 *     term put there would silently still be filtering the catalog days later;
 *   - a filtered catalog stays shareable and bookmarkable;
 *   - the browser Back button steps through filter changes for free.
 *
 * Both the AppBar search box and the CategoryPage filter panel go through here
 * so they cannot drift on parameter names.
 */

export const SORT_OPTIONS = [
    { value: '', label: 'Default' },
    { value: 'price_asc', label: 'Price: low to high' },
    { value: 'price_desc', label: 'Price: high to low' },
    { value: 'name_asc', label: 'Name: A–Z' },
    { value: 'name_desc', label: 'Name: Z–A' },
];

// Matches the values seeded into Product.recommended_climate.
export const CLIMATE_OPTIONS = ['Tropical', 'Temperate', 'Polar'];

export const EMPTY_FILTERS = {
    search: '',
    climate: '',
    min_price: '',
    max_price: '',
    sensitive_skin: false,
    in_stock: false,
    sort: '',
};

/** @param {string} queryString e.g. location.search */
export const parseProductQuery = (queryString) => {
    const params = new URLSearchParams(queryString || '');
    return {
        search: params.get('search') || '',
        climate: params.get('climate') || '',
        min_price: params.get('min_price') || '',
        max_price: params.get('max_price') || '',
        sensitive_skin: params.get('sensitive_skin') === 'true',
        in_stock: params.get('in_stock') === 'true',
        sort: params.get('sort') || '',
    };
};

/**
 * Serialize filters back to a query string, omitting anything at its default so
 * the URL stays short and a cleared filter panel gives a bare `/products`.
 *
 * @returns {string} '' or '?a=b&c=d'
 */
export const buildProductQuery = (filters) => {
    const params = new URLSearchParams();
    Object.entries(EMPTY_FILTERS).forEach(([key, empty]) => {
        const value = filters?.[key];
        if (value === undefined || value === null || value === empty) return;
        if (typeof empty === 'boolean') {
            if (value) params.set(key, 'true');
        } else if (String(value).trim() !== '') {
            params.set(key, String(value).trim());
        }
    });
    const qs = params.toString();
    return qs ? `?${qs}` : '';
};

/** True when any filter is set — drives the "Clear all" affordance. */
export const hasActiveFilters = (filters) =>
    Object.entries(EMPTY_FILTERS).some(
        ([key, empty]) => (filters?.[key] ?? empty) !== empty
    );

/**
 * Turn UI filter state into `GET /api/products` query params.
 *
 * Price is the one value that needs converting: the inputs are labelled with
 * the currency the shopper is browsing in, but `Product.price_amount` — and so
 * the API's min_price/max_price — is stored in USD.
 *
 * @param {object} filters      parsed filter state
 * @param {string} category     current category name
 * @param {number} [rateToUsd]  display currency's multiplier over USD
 */
export const toApiFilters = (filters, category, rateToUsd = 1) => {
    const rate = Number(rateToUsd) > 0 ? Number(rateToUsd) : 1;
    const toUsd = (value) => {
        const n = parseFloat(value);
        // Guards against '12abc' and, via the rate, a currency list that
        // predates the rate_to_usd field being returned.
        return Number.isFinite(n) ? Number((n / rate).toFixed(2)) : undefined;
    };

    return {
        category,
        search: filters.search || undefined,
        climate: filters.climate || undefined,
        min_price: filters.min_price !== '' ? toUsd(filters.min_price) : undefined,
        max_price: filters.max_price !== '' ? toUsd(filters.max_price) : undefined,
        sensitive_skin: filters.sensitive_skin || undefined,
        in_stock: filters.in_stock || undefined,
        sort: filters.sort || undefined,
    };
};
