import React, { Component } from 'react';
import './AppBar.scss';
import Logo from '../../Images/Logo.svg';
import ArrowDown from '../../Images/ArrowDown.svg';
import Cart from '../../Images/Cart.svg';
import { connect } from 'react-redux';
import CurrencySwitcher from '../CurrencySwitcher/CurrencySwitcher';
import MiniCart from '../MiniCart/MiniCart';
import { withRouter } from 'react-router-dom';
import { back_end_endpoint } from '../../Configs/BackEndEndpoint';
// Removed unused GraphQL query import

class AppBar extends Component {
    state = {
        openProfileDropdown: false
    }

    toggleProfileDropdown = (e) => {
        e.stopPropagation();
        this.setState(prevState => ({
            openProfileDropdown: !prevState.openProfileDropdown
        }));
    }

    closeProfileDropdown = () => {
        this.setState({ openProfileDropdown: false });
    }

    handleCloseAll = () => {
        this.closeProfileDropdown();
        this.props.handle_CloseCartOrCurr();
    }

    getdata = async () => {
        await fetch(back_end_endpoint() + "/api/categories")
            .catch(error => console.error(error))
            .then(async (res) => {
                const json_data = await res.json();
                const processed_data = json_data.map(c => c.name);
                this.props.setAllCategories(processed_data);
            })
    }

    componentDidMount = () => {
        this.getdata();
    }

    render() {
        return (
            <div className='appbar_main_max_w'>
                <div className='appbar_main'>
                    <span className='a_m_cat' onClick={this.handleCloseAll}>
                        {this.props.AllCategories?.length > 0 &&
                             this.props.AllCategories?.map((category, i) =>
                                <span
                                    key={i}
                                    className='a_m_cat_nl'
                                    id={i === this.props.CurrentCategory ? 'a_m_cat_nl' : ''}
                                    onClick={() => {
                                        this.props.setCurrentCategory(i);
                                        if (this.props.location?.pathname !== "/products") {
                                            this.props.history?.push(`/products`);
                                        }
                                    }}
                                >
                                    <p>{category.toUpperCase()}</p>
                                </span>
                            )}
                    </span>
                    <div className='a_m_img' onClick={this.handleCloseAll}>
                        <img
                            src={Logo}
                            alt='ScandiWeb_Logo'
                        />
                    </div>
                    <span className='a_m_cur_cart' onClick={this.handleCloseAll}>
                        <span
                            className="a_m_c_c_cur"
                            onClick={() => this.props.setOpenCurrSwitcher(!this.props.openCurrSwitcher)}
                        >
                            <p>{this.props.AllCurrencies?.length > 0 &&
                                this.props.AllCurrencies[this.props.CurrentCurrency]?.symbol
                            }</p>
                            <img
                                src={ArrowDown}
                                alt='Arr_Dwn'
                                id={this.props.openCurrSwitcher ? 'img' : ''}
                            />
                        </span>
                        <span
                            className='a_m_c_c_cart'
                            onClick={() => this.props.setOpenMiniCartOverlay(!this.props.openMiniCartOverlay)}
                        >
                            {this.props.TotalCarts > 0 &&
                                <p>{this.props.TotalCarts}</p>
                            }
                            <img
                                src={Cart}
                                alt='cart'
                            />
                        </span>
                        <span className="a_m_c_c_auth" style={{ marginLeft: "20px", display: "inline-flex", alignItems: "center", position: "relative" }}>
                            {localStorage.getItem('token') ? (
                                <div className="a_m_profile_dropdown_container">
                                    <button 
                                        className="profile_toggle_btn"
                                        onClick={this.toggleProfileDropdown}
                                    >
                                        My Profile
                                    </button>
                                    {this.state.openProfileDropdown && (
                                        <div className="profile_dropdown_menu">
                                            <div className="profile_email">
                                                {(() => {
                                                    try {
                                                        const user = JSON.parse(localStorage.getItem('user'));
                                                        return user?.email || 'User';
                                                    } catch(e) {
                                                        return 'User';
                                                    }
                                                })()}
                                            </div>
                                            <div className="profile_role">
                                                {localStorage.getItem('role') || 'buyer'}
                                            </div>
                                            <div className="profile_divider"></div>
                                            <button 
                                                className="profile_menu_btn"
                                                onClick={() => {
                                                    this.closeProfileDropdown();
                                                    const role = localStorage.getItem('role');
                                                    this.props.history?.push(role === 'supplier' ? '/supplier/dashboard' : '/buyer/dashboard');
                                                }}
                                            >
                                                Dashboard
                                            </button>
                                            <button 
                                                className="profile_logout_btn"
                                                onClick={() => {
                                                    this.closeProfileDropdown();
                                                    localStorage.clear();
                                                    this.props.history?.push('/login');
                                                }}
                                            >
                                                Log Out
                                            </button>
                                        </div>
                                    )}
                                </div>
                            ) : (
                                <button 
                                    onClick={() => this.props.history?.push('/login')}
                                    style={{
                                        background: 'none', border: '1px solid #1d1f22', padding: '6px 12px', borderRadius: '4px',
                                        fontSize: '13px', fontWeight: '600', textTransform: 'uppercase', cursor: 'pointer', outline: 'none'
                                    }}
                                >
                                    Sign In
                                </button>
                            )}
                        </span>
                    </span>
                    <div
                        className='a_m_cur_sw'
                        id={this.props.openCurrSwitcher ? 'a_m_cur_sw' : ''}
                    >
                        <CurrencySwitcher
                            handle_CloseCartOrCurr={this.handleCloseAll}
                        />
                    </div>
                    <div
                        className='a_m_minicart'
                        id={this.props.openMiniCartOverlay ? 'a_m_minicart' : ''}
                    >
                        <MiniCart
                            handle_CloseCartOrCurr={this.handleCloseAll}
                        />
                    </div>
                </div>
            </div>
        )
    }
}

const mapStateToProps = (state) => {
    return {
        AllCategories: state.AllCategories,
        CurrentCategory: state.CurrentCategory,
        AllCurrencies: state.AllCurrencies,
        CurrentCurrency: state.CurrentCurrency,
        TotalCarts: state.TotalCarts
    }
}

const mapDispatchToProps = (dispatch) => {
    return {
        setAllCategories: (all_cat) => dispatch({ type: "ALL_CATEGORIES", payload: all_cat }),
        setCurrentCategory: (current_cat) => dispatch({ type: "CURRENT_CATEGORY", payload: current_cat })
    }
}

export default (connect(mapStateToProps, mapDispatchToProps)(withRouter(AppBar)));


