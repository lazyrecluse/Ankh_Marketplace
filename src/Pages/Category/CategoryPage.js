import React, { Component } from 'react';
import './CategoryPage.scss';
import ArrowLeftBlack from '../../Images/ArrowLeftBlack.png';
import ProductCard from '../../Components/ProductCard/ProductCard';
import ProductFilters from './ProductFilters';
import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import { getProducts } from '../../Api/catalog';
import { getUser } from '../../Auth/session';
import {
    EMPTY_FILTERS,
    buildProductQuery,
    hasActiveFilters,
    parseProductQuery,
    toApiFilters,
} from '../../Utils/productQuery';

class CategoryPage extends Component {
    constructor(props) {
        super(props)

        this.state = {
            max_product_per_page: 6,
            p_first_index: 0,
            p_last_index: 6,
            l_error: false
        }
    }

    goToPage = (pageNumber) => {
        const totalPages = Math.ceil((this.props.ProductList?.length || 0) / this.state.max_product_per_page) || 1;
        const clampedPage = Math.max(1, Math.min(pageNumber, totalPages));
        const p_first_index = (clampedPage - 1) * this.state.max_product_per_page;
        const p_last_index = clampedPage * this.state.max_product_per_page;
        this.setState({ p_first_index, p_last_index });
        window.scrollTo(0, 0);
    }

    decreaseProductFilter = () => {
        if (this.state.p_first_index > 0) {
            this.setState({ p_first_index: this.state.p_first_index - this.state.max_product_per_page, p_last_index: this.state.p_last_index - this.state.max_product_per_page });
        }
        window.scrollTo(0, 0);
    }

    increaseProductFilter = () => {
        if (this.state.p_last_index < this.props.ProductList?.length) {
            this.setState({ p_first_index: this.state.p_first_index + this.state.max_product_per_page, p_last_index: this.state.p_last_index + this.state.max_product_per_page });
        }
        window.scrollTo(0, 0);
    }

    getdata = () => {
        const load_products = async () => {
            const urlFilters = parseProductQuery(this.props.location?.search);

            // A buyer's onboarding preferences seed the catalog, but only where
            // the shopper has not chosen for themselves — an explicit filter in
            // the URL always wins, otherwise clearing one would appear to do
            // nothing for buyers who set a preference at signup.
            const user = getUser();
            const effective = { ...urlFilters };
            if (user?.profile) {
                if (
                    !effective.climate &&
                    user.profile.preferred_climate &&
                    user.profile.preferred_climate !== 'All'
                ) {
                    effective.climate = user.profile.preferred_climate;
                }
                if (!effective.sensitive_skin && user.profile.has_sensitive_skin) {
                    effective.sensitive_skin = true;
                }
            }

            const category = this.props.AllCategories[this.props.CurrentCategory];
            const rate = this.props.AllCurrencies?.[this.props.CurrentCurrency]?.rate_to_usd;

            try {
                const json_data = await getProducts(toApiFilters(effective, category, rate));
                this.props.SetProductList(json_data);
                this.setState({
                    p_first_index: 0,
                    p_last_index: this.state.max_product_per_page,
                    l_error: false
                });
            } catch (error) {
                this.setState({ l_error: true });
                console.error(error);
            }
        }

        if (this.props.AllCategories.length > 0) {
            load_products();
        } else {
            // Waits for 2.5s for the category name to load
            setTimeout(() => {
                if (this.props.AllCategories.length > 0) {
                    load_products();
                } else {
                    setTimeout(() => {
                        // Waits for 3s for the category name to load
                        load_products();
                    }, 3000)
                }
            }, 2500)
        }
    }

    handle_Update = () => {
        this.setState({ l_error: false });
        this.props.ClearProductList();
        document.title = `ScandiStore ${this.props.AllCategories?.length > 0 ? '|' : ''} ${this.props.AllCategories?.length > 0 ? this.props.AllCategories[this.props.CurrentCategory][0]?.toUpperCase() : ''}${this.props.AllCategories?.length > 0 ? this.props.AllCategories[this.props.CurrentCategory]?.slice(1).toLowerCase() : ''}`;
        this.getdata();
        window.scrollTo(0, 0);
    }

    componentDidMount = () => {
        this.handle_Update();
    }

    componentDidUpdate = (prevProps) => {
        // The query string drives the filters, so a change to it is as much a
        // reason to refetch as a category change. Currency matters because the
        // price filter is typed in the displayed currency and converted to USD
        // before it reaches the API.
        if (
            prevProps.CurrentCategory !== this.props.CurrentCategory ||
            prevProps.location?.search !== this.props.location?.search ||
            prevProps.CurrentCurrency !== this.props.CurrentCurrency
        ) {
            this.handle_Update();
        } else if (this.state.error) {
            this.handle_Update();
        }
    }

    applyFilters = (filters) => {
        // Push rather than replace: Back should step through filter changes.
        this.props.history.push(`/products${buildProductQuery(filters)}`);
        window.scrollTo(0, 0);
    }

    render() {
        const totalPages = Math.ceil((this.props.ProductList?.length || 0) / this.state.max_product_per_page) || 1;
        const currentPage = Math.floor(this.state.p_first_index / this.state.max_product_per_page) + 1;
        const currentCatName = this.props.AllCategories?.length > 0 ? this.props.AllCategories[this.props.CurrentCategory] : "";

        const urlFilters = parseProductQuery(this.props.location?.search);
        const filtersActive = hasActiveFilters(urlFilters);
        const currency = this.props.AllCurrencies?.[this.props.CurrentCurrency];
        const resultCount = this.props.ProductList?.length || 0;

        return (
            <main
                className='categorypage_main'
                onClick={this.props.handle_CloseCartOrCurr}
            >
                {currentCatName === "all" && !filtersActive && (
                    <div className="category_tiles_container">
                        <h2 className="ct_title">Browse by Category</h2>
                        <div className="ct_grid">
                            {this.props.AllCategories.map((cat, idx) => {
                                if (cat === "all") return null;
                                const coverImages = {
                                    cotton: "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=800",
                                    silk: "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=800",
                                    linen: "https://images.unsplash.com/photo-1606744824163-985d376605aa?w=800",
                                    // Absolute URLs, matching seed.py: the previous
                                    // /static/uploads/*.jpg paths point into a
                                    // gitignored directory, so they 404 on any fresh
                                    // deploy.
                                    woolen: "https://images.unsplash.com/photo-1520903920243-00d872a2d1c9?w=800",
                                    mohair: "https://images.unsplash.com/photo-1565084888279-aca607ecce0c?w=800",
                                    ankara: "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=800",
                                    kente: "https://images.unsplash.com/photo-1596993100471-c3905dafa78e?w=800",
                                    velvet: "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=800",
                                    cashmere: "https://images.unsplash.com/photo-1551232864-3f0890e580d9?w=800"
                                };
                                return (
                                    <div 
                                        key={idx} 
                                        className={`ct_tile ct_tile_${cat}`}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            const index = this.props.AllCategories.indexOf(cat);
                                            if (index !== -1) {
                                                this.props.setCurrentCategory(index);
                                            }
                                        }}
                                    >
                                        <div className="ct_tile_overlay"></div>
                                        <img src={coverImages[cat] || coverImages.cotton} alt={cat} className="ct_tile_img" />
                                        <h3 className="ct_tile_name">{cat.toUpperCase()}</h3>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                )}
                <div className='cp_m_layout'>
                <ProductFilters
                    filters={urlFilters}
                    currencySymbol={currency?.symbol || '$'}
                    onApply={this.applyFilters}
                />
                <div className='cp_m_results'>
                {this.props.ProductList?.length > 0 && <div>
                    <h1 className='cp_m_h1'>
                        {currentCatName[0]?.toUpperCase()}
                        {currentCatName?.slice(1).toLowerCase()}
                        <span className='cp_m_count'>
                            {resultCount} {resultCount === 1 ? 'product' : 'products'}
                            {urlFilters.search ? ` for “${urlFilters.search}”` : ''}
                        </span>
                    </h1>
                    <div className='cp_m_product_w'>
                        {this.props.ProductList?.length > 0 &&
                            this.props.ProductList?.slice(this.state.p_first_index, this.state.p_last_index)?.map((item, i) =>
                                <ProductCard key={i} product_info={item} />
                            )
                        }
                    </div>
                    <div className='cp_m_pagination'>
                        <img
                            src={ArrowLeftBlack}
                            alt='<'
                            onClick={this.decreaseProductFilter}
                        />
                        {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                            <button
                                key={pageNum}
                                className={`page_btn ${currentPage === pageNum ? 'active-page' : ''}`}
                                onClick={() => this.goToPage(pageNum)}
                            >
                                {pageNum}
                            </button>
                        ))}
                        <img
                            className='cp_m_p_ar'
                            src={ArrowLeftBlack}
                            alt='>'
                            onClick={this.increaseProductFilter}
                        />
                    </div>
                </div>
                }
                {(!this.props.ProductList || this.props.ProductList.length === 0) && this.state.l_error === false &&
                    <div className='no_products_view'>
                        <p>
                            {filtersActive
                                ? 'No products match these filters.'
                                : 'No products found in this category.'}
                        </p>
                        {filtersActive &&
                            <button
                                className='no_products_clear'
                                onClick={() => this.applyFilters(EMPTY_FILTERS)}
                            >
                                Clear filters
                            </button>
                        }
                    </div>
                }
                {this.state.l_error === true &&
                    <p className='cp_m_loading' id='cp_m_loading'>Error Loading Products...</p>
                }
                </div>
                </div>
            </main>
        )
    }
}

const mapStateToProps = (state) => {
    return {
        AllCategories: state.AllCategories,
        CurrentCategory: state.CurrentCategory,
        AllCurrencies: state.AllCurrencies,
        CurrentCurrency: state.CurrentCurrency,
        ProductList: state.ProductList
    }
}

const mapDispatchToProps = (dispatch) => {
    return {
        SetProductList: (p_list) => dispatch({ type: 'SET_PRODUCT_LIST', payload: p_list }),
        ClearProductList: () => dispatch({ type: 'CLEAR_PRODUCT_LIST' }),
        setCurrentCategory: (current_cat) => dispatch({ type: "CURRENT_CATEGORY", payload: current_cat })
    }
}

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(CategoryPage));
