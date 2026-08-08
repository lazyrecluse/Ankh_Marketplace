import React, { useState } from 'react';
import './ProductFilters.scss';
import {
    CLIMATE_OPTIONS,
    EMPTY_FILTERS,
    SORT_OPTIONS,
    hasActiveFilters,
} from '../../Utils/productQuery';

/**
 * Filter panel for the catalog page.
 *
 * Owns its own draft state and only reports back via onApply — typing in the
 * price box must not fire a backend request per keystroke, and the URL is the
 * single source of truth, written only when the shopper submits. Props:
 *
 * @param {object}   filters       parsed from the URL by the parent
 * @param {string}   currencySymbol e.g. '$' — labels the price inputs, which
 *                                 are typed in the displayed currency and
 *                                 converted to the API's USD by the parent
 * @param {Function} onApply(mergedFilters) — parent pushes the new URL
 */
const ProductFilters = ({ filters = EMPTY_FILTERS, currencySymbol = '$', onApply }) => {
    const [draft, setDraft] = useState(filters);
    const [open, setOpen] = useState(false);

    // The URL is the source of truth; when the parent sees a change in it
    // (search from the AppBar, a category tile, Back/Forward), the panel's
    // draft must follow or it would show stale values. This is React's
    // "adjust state when props change" pattern — setSyncedKey has to be part
    // of it, otherwise the comparison never settles and re-renders forever.
    const key = JSON.stringify(filters);
    const [syncedKey, setSyncedKey] = useState(key);
    if (key !== syncedKey) {
        setSyncedKey(key);
        setDraft(filters);
    }

    const set = (key) => (event) => {
        const value =
            event.target.type === 'checkbox' ? event.target.checked : event.target.value;
        setDraft((d) => ({ ...d, [key]: value }));
    };

    const submit = (event) => {
        event.preventDefault();
        onApply(draft);
        setOpen(false);
    };

    const clearAll = () => {
        setDraft(EMPTY_FILTERS);
        onApply(EMPTY_FILTERS);
    };

    return (
        <aside className={`pf_panel ${open ? 'pf_panel_open' : ''}`}>
            <button
                type="button"
                className="pf_toggle"
                onClick={() => setOpen((o) => !o)}
                aria-expanded={open}
                aria-controls="pf_filters"
            >
                <span>Filters</span>
                {hasActiveFilters(filters) && <span className="pf_active_dot" aria-label="filters active" />}
                <span className="pf_toggle_chevron">{open ? '−' : '+'}</span>
            </button>

            <div className="pf_body" id="pf_filters">
                <form onSubmit={submit}>
                    <label className="pf_field">
                        <span className="pf_label">Search</span>
                        <input
                            type="search"
                            value={draft.search}
                            onChange={set('search')}
                            placeholder="Name, brand, description…"
                        />
                    </label>

                    <div className="pf_row">
                        <label className="pf_field">
                            <span className="pf_label">Min price ({currencySymbol})</span>
                            <input
                                type="number"
                                min="0"
                                step="0.01"
                                value={draft.min_price}
                                onChange={set('min_price')}
                                placeholder="0"
                            />
                        </label>
                        <label className="pf_field">
                            <span className="pf_label">Max price ({currencySymbol})</span>
                            <input
                                type="number"
                                min="0"
                                step="0.01"
                                value={draft.max_price}
                                onChange={set('max_price')}
                                placeholder="∞"
                            />
                        </label>
                    </div>

                    <label className="pf_field">
                        <span className="pf_label">Climate</span>
                        <select value={draft.climate} onChange={set('climate')}>
                            <option value="">All climates</option>
                            {CLIMATE_OPTIONS.map((c) => (
                                <option key={c} value={c}>{c}</option>
                            ))}
                        </select>
                    </label>

                    <label className="pf_field">
                        <span className="pf_label">Sort by</span>
                        <select value={draft.sort} onChange={set('sort')}>
                            {SORT_OPTIONS.map((o) => (
                                <option key={o.value} value={o.value}>{o.label}</option>
                            ))}
                        </select>
                    </label>

                    <div className="pf_checks">
                        <label className="pf_check">
                            <input
                                type="checkbox"
                                checked={draft.sensitive_skin}
                                onChange={set('sensitive_skin')}
                            />
                            <span>Sensitive skin only</span>
                        </label>
                        <label className="pf_check">
                            <input
                                type="checkbox"
                                checked={draft.in_stock}
                                onChange={set('in_stock')}
                            />
                            <span>In stock only</span>
                        </label>
                    </div>

                    <div className="pf_actions">
                        <button type="submit" className="pf_apply">Apply</button>
                        <button type="button" className="pf_clear" onClick={clearAll}>
                            Clear all
                        </button>
                    </div>
                </form>
            </div>
        </aside>
    );
};

export default ProductFilters;
