import React, { Component } from 'react';
import './CategoryPage.scss';
import ArrowLeftBlack from '../../Images/ArrowLeftBlack.png';
import ProductCard from '../../Components/ProductCard/ProductCard';
import { connect } from 'react-redux';
import { getProducts } from '../../Api/catalog';
import { resolveImageUrl } from '../../Api/client';
import { getUser } from '../../Auth/session';

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
            const filters = {
                category: this.props.AllCategories[this.props.CurrentCategory]
            };

            // Buyers get their onboarding preferences applied as filters.
            const user = getUser();
            if (user?.profile) {
                if (user.profile.preferred_climate && user.profile.preferred_climate !== "All") {
                    filters.climate = user.profile.preferred_climate;
                }
                if (user.profile.has_sensitive_skin) {
                    filters.sensitive_skin = true;
                }
            }

            try {
                const json_data = await getProducts(filters);
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
        if (prevProps.CurrentCategory !== this.props.CurrentCategory) {
            this.handle_Update();
        } else {
            if (this.state.error) {
                this.handle_Update();
            }
        }
    }

    render() {
        const totalPages = Math.ceil((this.props.ProductList?.length || 0) / this.state.max_product_per_page) || 1;
        const currentPage = Math.floor(this.state.p_first_index / this.state.max_product_per_page) + 1;
        const currentCatName = this.props.AllCategories?.length > 0 ? this.props.AllCategories[this.props.CurrentCategory] : "";

        return (
            <main
                className='categorypage_main'
                onClick={this.props.handle_CloseCartOrCurr}
            >
                {currentCatName === "all" && (
                    <div className="category_tiles_container">
                        <h2 className="ct_title">Browse by Category</h2>
                        <div className="ct_grid">
                            {this.props.AllCategories.map((cat, idx) => {
                                if (cat === "all") return null;
                                const coverImages = {
                                    cotton: "https://images.unsplash.com/photo-1598033129183-c4f50c736f10?w=800",
                                    silk: "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=800",
                                    linen: "https://images.unsplash.com/photo-1606744824163-985d376605aa?w=800",
                                    woolen: resolveImageUrl("/static/uploads/woolen_fabric_1.jpg"),
                                    mohair: resolveImageUrl("/static/uploads/mohair_fabric_1.jpg"),
                                    ankara: resolveImageUrl("/static/uploads/ankara_fabric_1.jpg"),
                                    kente: resolveImageUrl("/static/uploads/kente_fabric_1.jpg"),
                                    velvet: resolveImageUrl("/static/uploads/velvet_fabric_1.jpg"),
                                    cashmere: resolveImageUrl("/static/uploads/cashmere_fabric_1.jpg")
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
                {this.props.ProductList?.length > 0 && <div>
                    <h1 className='cp_m_h1'>
                        {currentCatName[0]?.toUpperCase()}
                        {currentCatName?.slice(1).toLowerCase()}
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
                    <div className='no_products_view'><p>No products found in this category.</p></div>
                }
                {this.state.l_error === true &&
                    <p className='cp_m_loading' id='cp_m_loading'>Error Loading Products...</p>
                }
            </main>
        )
    }
}

const mapStateToProps = (state) => {
    return {
        AllCategories: state.AllCategories,
        CurrentCategory: state.CurrentCategory,
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

export default (connect(mapStateToProps, mapDispatchToProps)(CategoryPage));
