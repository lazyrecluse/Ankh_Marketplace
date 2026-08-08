import React, { useCallback, useEffect, useRef, useState } from 'react';
import { useHistory, useLocation } from 'react-router-dom';
import './SearchBar.scss';
import SearchIcon from '../../Images/Search.svg';
import { buildProductQuery, parseProductQuery } from '../../Utils/productQuery';

/**
 * The AppBar search affordance: an icon that expands into a text input.
 *
 * Submitting navigates to /products with `search` set, preserving whatever
 * other filters are already in the URL so a search does not silently reset the
 * shopper's price range or sort. The catalog page reads the query string, so
 * there is no shared state between the two beyond the URL itself.
 */
const SearchBar = ({ onBeforeOpen }) => {
    const history = useHistory();
    const location = useLocation();

    const [open, setOpen] = useState(false);
    const [term, setTerm] = useState('');
    const inputRef = useRef(null);
    const containerRef = useRef(null);

    // Keep the box in step with the URL, so a Back/Forward step or a filter
    // cleared from the panel is reflected here too.
    useEffect(() => {
        setTerm(parseProductQuery(location.search).search);
    }, [location.search]);

    useEffect(() => {
        if (open) inputRef.current?.focus();
    }, [open]);

    const collapseIfEmpty = useCallback(() => {
        setOpen((wasOpen) => (inputRef.current?.value ? wasOpen : false));
    }, []);

    // Clicking anywhere else closes an empty box; a box with a term stays open
    // so the shopper can see what is being searched for.
    useEffect(() => {
        if (!open) return undefined;
        const onDocumentClick = (event) => {
            if (!containerRef.current?.contains(event.target)) collapseIfEmpty();
        };
        document.addEventListener('mousedown', onDocumentClick);
        return () => document.removeEventListener('mousedown', onDocumentClick);
    }, [open, collapseIfEmpty]);

    const submit = (event) => {
        event?.preventDefault();
        event?.stopPropagation();

        // Preserve the other filters; only `search` is being changed here.
        const next = { ...parseProductQuery(location.search), search: term.trim() };
        history.push(`/products${buildProductQuery(next)}`);
        window.scrollTo(0, 0);
    };

    const handleIconClick = (event) => {
        event.stopPropagation();
        if (!open) {
            // Close the mini-cart / currency dropdown first — they overlap.
            onBeforeOpen?.();
            setOpen(true);
            return;
        }
        submit(event);
    };

    const handleKeyDown = (event) => {
        if (event.key === 'Escape') {
            setTerm('');
            setOpen(false);
            inputRef.current?.blur();
        }
    };

    return (
        <form
            className={`searchbar ${open ? 'searchbar_open' : ''}`}
            ref={containerRef}
            onSubmit={submit}
            onClick={(e) => e.stopPropagation()}
            role="search"
        >
            <input
                ref={inputRef}
                type="search"
                className="searchbar_input"
                placeholder="Search fabrics, brands…"
                aria-label="Search products"
                value={term}
                onChange={(e) => setTerm(e.target.value)}
                onKeyDown={handleKeyDown}
                tabIndex={open ? 0 : -1}
            />
            <button
                type="button"
                className="searchbar_btn"
                onClick={handleIconClick}
                aria-label={open ? 'Submit search' : 'Open search'}
                aria-expanded={open}
            >
                <img src={SearchIcon} alt="" />
            </button>
        </form>
    );
};

export default SearchBar;
