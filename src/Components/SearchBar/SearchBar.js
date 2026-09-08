import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useHistory, useLocation } from 'react-router-dom';
import './SearchBar.scss';
import SearchIcon from '../../Images/Search.svg';
import {
    CLIMATE_OPTIONS,
    EMPTY_FILTERS,
    SORT_OPTIONS,
    buildProductQuery,
    parseProductQuery,
} from '../../Utils/productQuery';

const HISTORY_STORAGE_KEY = 'ankh_session_search_history';

const loadSessionHistory = () => {
    try {
        const raw = sessionStorage.getItem(HISTORY_STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
    } catch {
        return [];
    }
};

const saveSessionHistory = (query) => {
    const q = (query || '').trim();
    if (!q) return;
    try {
        const current = loadSessionHistory();
        const next = [q, ...current.filter((item) => item.toLowerCase() !== q.toLowerCase())].slice(0, 6);
        sessionStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(next));
    } catch (e) {
        console.error(e);
    }
};

const clearSessionHistory = () => {
    try {
        sessionStorage.removeItem(HISTORY_STORAGE_KEY);
    } catch (e) {
        console.error(e);
    }
};

/**
 * Enhanced SearchBar:
 * - Expands on click with a blurred backdrop over the main page.
 * - Displays recent search history from the current session.
 * - Includes a 3-lines filter widget to filter directly in the search bar.
 */
const SearchBar = ({ onBeforeOpen, currencySymbol = '$' }) => {
    const history = useHistory();
    const location = useLocation();

    const [open, setOpen] = useState(false);
    const [term, setTerm] = useState('');
    const [showFilters, setShowFilters] = useState(false);
    const [draftFilters, setDraftFilters] = useState(EMPTY_FILTERS);
    const [historyList, setHistoryList] = useState([]);

    const inputRef = useRef(null);
    const containerRef = useRef(null);

    // Sync search input and filters with current URL query params
    useEffect(() => {
        const parsed = parseProductQuery(location.search);
        setTerm(parsed.search || '');
        setDraftFilters(parsed);
    }, [location.search]);

    // Load session search history on mount and when opening
    useEffect(() => {
        setHistoryList(loadSessionHistory());
    }, [open]);

    useEffect(() => {
        if (open) {
            inputRef.current?.focus();
        }
    }, [open]);

    const handleClose = useCallback(() => {
        setOpen(false);
        setShowFilters(false);
    }, []);

    // Close on escape key
    const handleKeyDown = (event) => {
        if (event.key === 'Escape') {
            handleClose();
            inputRef.current?.blur();
        }
    };

    const submitWithParams = (searchTerm, filtersToApply) => {
        const trimmed = (searchTerm !== undefined ? searchTerm : term).trim();
        if (trimmed) {
            saveSessionHistory(trimmed);
            setHistoryList(loadSessionHistory());
        }

        const next = {
            ...(filtersToApply || draftFilters),
            search: trimmed,
        };

        history.push(`/products${buildProductQuery(next)}`);
        window.scrollTo(0, 0);
        handleClose();
    };

    const handleSubmit = (event) => {
        event?.preventDefault();
        event?.stopPropagation();
        submitWithParams(term, draftFilters);
    };

    const handleSelectHistory = (historyItem) => {
        setTerm(historyItem);
        submitWithParams(historyItem, draftFilters);
    };

    const handleClearHistory = (e) => {
        e.stopPropagation();
        clearSessionHistory();
        setHistoryList([]);
    };

    const handleResetFilters = (e) => {
        e.stopPropagation();
        setDraftFilters({
            ...EMPTY_FILTERS,
            search: term,
        });
    };

    const handleOpenSearch = (e) => {
        e.stopPropagation();
        if (!open) {
            onBeforeOpen?.();
            setOpen(true);
        }
    };

    const activeFilterCount = Object.keys(EMPTY_FILTERS).filter(
        (k) => k !== 'search' && draftFilters[k] !== EMPTY_FILTERS[k]
    ).length;

    return (
        <div className="searchbar_wrapper">
            {/* Blurred backdrop covering the main page when search is expanded */}
            {open && (
                <div
                    className="searchbar_backdrop"
                    onClick={handleClose}
                    aria-hidden="true"
                />
            )}

            <div
                className={`searchbar ${open ? 'searchbar_open' : ''}`}
                ref={containerRef}
                onClick={(e) => e.stopPropagation()}
                role="search"
            >
                <form className="searchbar_input_row" onSubmit={handleSubmit}>
                    <button
                        type="button"
                        className="searchbar_btn searchbar_icon_btn"
                        onClick={handleOpenSearch}
                        aria-label="Open search"
                    >
                        <img src={SearchIcon} alt="" />
                    </button>

                    <input
                        ref={inputRef}
                        type="search"
                        className="searchbar_input"
                        placeholder="Search fabrics, categories, brands…"
                        aria-label="Search products"
                        value={term}
                        onFocus={handleOpenSearch}
                        onChange={(e) => setTerm(e.target.value)}
                        onKeyDown={handleKeyDown}
                        tabIndex={0}
                    />

                    {/* Clear text button */}
                    {term && open && (
                        <button
                            type="button"
                            className="searchbar_clear_term_btn"
                            onClick={() => {
                                setTerm('');
                                inputRef.current?.focus();
                            }}
                            title="Clear input"
                        >
                            ✕
                        </button>
                    )}

                    {/* 3-lines filter widget */}
                    {open && (
                        <button
                            type="button"
                            className={`searchbar_filter_toggle_btn ${showFilters ? 'active' : ''} ${activeFilterCount > 0 ? 'has_filters' : ''}`}
                            onClick={(e) => {
                                e.stopPropagation();
                                setShowFilters((prev) => !prev);
                            }}
                            title="Filter specifications"
                            aria-label="Toggle filters"
                        >
                            {/* 3-lines filter icon with adjustment sliders */}
                            <svg
                                width="18"
                                height="18"
                                viewBox="0 0 24 24"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="2.2"
                                strokeLinecap="round"
                                strokeLinejoin="round"
                            >
                                <line x1="4" y1="6" x2="20" y2="6" />
                                <line x1="4" y1="12" x2="20" y2="12" />
                                <line x1="4" y1="18" x2="20" y2="18" />
                                <circle cx="8" cy="6" r="2" fill="currentColor" />
                                <circle cx="16" cy="12" r="2" fill="currentColor" />
                                <circle cx="10" cy="18" r="2" fill="currentColor" />
                            </svg>
                            {activeFilterCount > 0 && (
                                <span className="searchbar_filter_badge">{activeFilterCount}</span>
                            )}
                        </button>
                    )}

                    {/* Submit arrow / search button */}
                    {open && (
                        <button
                            type="submit"
                            className="searchbar_submit_btn"
                            aria-label="Submit search"
                        >
                            ➔
                        </button>
                    )}
                </form>

                {/* Expanded Dropdown Panel: History + Filters */}
                {open && (
                    <div className="searchbar_dropdown_card">
                        {/* Session Search History */}
                        {historyList.length > 0 && (
                            <div className="searchbar_history_section">
                                <div className="searchbar_section_header">
                                    <span className="searchbar_section_title">Recent Searches</span>
                                    <button
                                        type="button"
                                        className="searchbar_text_btn"
                                        onClick={handleClearHistory}
                                    >
                                        Clear History
                                    </button>
                                </div>
                                <div className="searchbar_history_chips">
                                    {historyList.map((item, idx) => (
                                        <button
                                            key={idx}
                                            type="button"
                                            className="searchbar_history_chip"
                                            onClick={() => handleSelectHistory(item)}
                                        >
                                            <span className="chip_clock">🕒</span>
                                            <span>{item}</span>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Filter Drawer toggled by the 3-lines widget */}
                        {showFilters && (
                            <div className="searchbar_filters_drawer">
                                <div className="searchbar_section_header">
                                    <span className="searchbar_section_title">Filter Specifications</span>
                                    <button
                                        type="button"
                                        className="searchbar_text_btn"
                                        onClick={handleResetFilters}
                                    >
                                        Reset
                                    </button>
                                </div>

                                <div className="searchbar_filter_grid">
                                    <div className="searchbar_filter_field">
                                        <label>Climate</label>
                                        <select
                                            value={draftFilters.climate || ''}
                                            onChange={(e) =>
                                                setDraftFilters((d) => ({ ...d, climate: e.target.value }))
                                            }
                                        >
                                            <option value="">All Climates</option>
                                            {CLIMATE_OPTIONS.map((c) => (
                                                <option key={c} value={c}>
                                                    {c}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    <div className="searchbar_filter_field">
                                        <label>Sort By</label>
                                        <select
                                            value={draftFilters.sort || ''}
                                            onChange={(e) =>
                                                setDraftFilters((d) => ({ ...d, sort: e.target.value }))
                                            }
                                        >
                                            {SORT_OPTIONS.map((o) => (
                                                <option key={o.value} value={o.value}>
                                                    {o.label}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    <div className="searchbar_filter_field">
                                        <label>Min Price ({currencySymbol})</label>
                                        <input
                                            type="number"
                                            min="0"
                                            step="0.01"
                                            placeholder="0"
                                            value={draftFilters.min_price || ''}
                                            onChange={(e) =>
                                                setDraftFilters((d) => ({ ...d, min_price: e.target.value }))
                                            }
                                        />
                                    </div>

                                    <div className="searchbar_filter_field">
                                        <label>Max Price ({currencySymbol})</label>
                                        <input
                                            type="number"
                                            min="0"
                                            step="0.01"
                                            placeholder="∞"
                                            value={draftFilters.max_price || ''}
                                            onChange={(e) =>
                                                setDraftFilters((d) => ({ ...d, max_price: e.target.value }))
                                            }
                                        />
                                    </div>
                                </div>

                                <div className="searchbar_filter_checks">
                                    <label className="searchbar_check_item">
                                        <input
                                            type="checkbox"
                                            checked={Boolean(draftFilters.sensitive_skin)}
                                            onChange={(e) =>
                                                setDraftFilters((d) => ({
                                                    ...d,
                                                    sensitive_skin: e.target.checked,
                                                }))
                                            }
                                        />
                                        <span>Sensitive skin only</span>
                                    </label>
                                    <label className="searchbar_check_item">
                                        <input
                                            type="checkbox"
                                            checked={Boolean(draftFilters.in_stock)}
                                            onChange={(e) =>
                                                setDraftFilters((d) => ({
                                                    ...d,
                                                    in_stock: e.target.checked,
                                                }))
                                            }
                                        />
                                        <span>In stock only</span>
                                    </label>
                                </div>
                            </div>
                        )}

                        {/* Search and apply action row */}
                        <div className="searchbar_actions_row">
                            <span className="searchbar_hint">Press Enter ↵ or click search</span>
                            <button
                                type="button"
                                className="searchbar_apply_btn"
                                onClick={handleSubmit}
                            >
                                Search & Apply Filters
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default SearchBar;
