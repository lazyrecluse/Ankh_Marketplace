import React, { Component } from 'react';
import './CartItem.scss';
import { connect } from 'react-redux';
import styled from 'styled-components';
import ArrowLeft from '../../Images/ArrowLeft.png';
import AddSign from '../../Images/AddSign.png';
import SubtractSign from '../../Images/SubtractSign.png';
import { resolveImageUrl } from '../../Api/client';

class CartItem extends Component {
    constructor(props) {
        super(props)
        this.state = {
            gallery_index: 0
        }
    }

    increaseProductCount = () => {
        const prevData = this.props.UserCarts[this.props.cart_index];
        const newData = { ...prevData, quantity: prevData?.quantity < 1 ? 1 : prevData?.quantity + 1 };
        this.props.UpdateUserCart(this.props.cart_index, { ...newData });
    }

    decreaseProductCount = () => {
        const prevData = this.props.UserCarts[this.props.cart_index];
        const newData = { ...prevData, quantity: prevData?.quantity <= 1 ? 1 : prevData?.quantity - 1 };
        this.props.UpdateUserCart(this.props.cart_index, { ...newData });
    }

    incrementGalleryIndex = () => {
        const MaxIndex = this.props.cart_info?.gallery?.length > 0 ? parseInt(this.props.cart_info?.gallery?.length) - 1 : 0;
        if (MaxIndex === 0) {
            this.setState({ gallery_index: 0 });
        } else if (this.state.gallery_index >= MaxIndex) {
            this.setState({ gallery_index: 0 });
        } else {
            this.setState({ gallery_index: this.state.gallery_index + 1 });
        }
    }

    decrementGalleryIndex = () => {
        const MaxIndex = this.props.cart_info?.gallery?.length > 0 ? parseInt(this.props.cart_info?.gallery?.length) - 1 : 0;
        if (MaxIndex === 0) {
            this.setState({ gallery_index: 0 });
        } else if (this.state.gallery_index <= 0) {
            this.setState({ gallery_index: MaxIndex });
        } else {
            this.setState({ gallery_index: this.state.gallery_index - 1 });
        }
    }

    handleSubTotalCalc = () => {
        const price = this.handlePriceBasedOnCurr()
        const quantity = this.props.cart_info?.quantity;
        const subtotal = price * quantity;
        const stringify_subtotal = subtotal.toString();
        const sub_total_to_2dp = parseFloat(stringify_subtotal).toFixed(2);
        return sub_total_to_2dp;
    }

    handlePriceBasedOnCurr = () => {
        if (this.props.cart_info?.prices?.length > 0) {
            const current_currency_symbol = this.props.AllCurrencies[this.props.CurrentCurrency]?.symbol || "$";
            const currency_obj = this.props.cart_info?.prices?.filter(item => item?.currency?.symbol === current_currency_symbol);
            const amt = currency_obj[0]?.amount;
            if (amt !== undefined && amt !== null) return parseFloat(amt).toFixed(2);
            const firstPrice = this.props.cart_info?.prices[0]?.amount;
            return firstPrice !== undefined ? parseFloat(firstPrice).toFixed(2) : '0.00';
        }
        return '0.00';
    }

    getProductAttributes = () => {
        const attrib = this.props.UserCarts?.filter(item => item.id === this.props.cart_info?.id);
        return attrib[0]?.attributes;
    }

    handle_Remove_Cart_Item = () => {
        this.props.RemoveCartItem(this.props.cart_index);
    }

    render() {
        const CartPACMiniT = styled.div`
            background: ${props => props.bgc_value};
            width: 16px;
            min-width: 16px;
            height: 16px;
            min-height: 16px;
        `;

        const CartPACMiniF = styled.div`
            background: ${props => props.bgc_value};
            width: 32px;
            min-width: 32px;
            height: 32px;
            min-height: 32px;

            @media (max-width:720px) {
                width: 22px;
                min-width: 22px;
                height: 22px;
                min-height: 22px;
            }
        `;

        return (
            <section className='cart_item_main' id={this.props.isMini ? '' : 'cart_item_main'}>
                <div className='ci_m_w'>
                    <span className='ci_m_1'>
                        <p className='ci_m_1_p cp_m_1_p_b'>{this.props.cart_info?.brand ? this.props.cart_info?.brand : ''}</p>
                        <p className='ci_m_1_p'>{this.props.cart_info?.name ? this.props.cart_info?.name : ''}</p>
                        <h4 className='ci_m_1_h4'>
                            {this.props.AllCurrencies?.[this.props.CurrentCurrency]?.symbol || '$'}
                            {this.handlePriceBasedOnCurr() === undefined ? '' : this.handlePriceBasedOnCurr()}
                        </h4>
                        {this.getProductAttributes()?.length > 0 &&
                            this.getProductAttributes()?.map((item, i) =>
                                <div key={i} className='ci_m_1_a_w'>
                                    <p className='ci_m_1_a_w_h'>{`${item?.name}:`}</p>
                                    <div className='ci_m_1_a_w_b'>
                                        {item?.type === "text" &&
                                            item?.items?.length > 0 &&
                                            item.items?.map((values, index) =>
                                                <h3
                                                    key={index}
                                                    id={values?.value === this.props.UserCarts?.[this.props.cart_index]?.[item?.name] ? 'h3' : ''}
                                                >{values?.value}</h3>
                                            )
                                        }
                                        {item?.type === "swatch" &&
                                            item?.items?.length > 0 &&
                                            item?.items?.map((values, index) =>
                                                <span
                                                    key={index}
                                                    id={values?.value === this.props.UserCarts?.[this.props.cart_index]?.[item?.name] ? 'span' : ''}
                                                >
                                                    {this.props.isMini &&
                                                        <CartPACMiniT
                                                            bgc_value={values?.value}
                                                        >
                                                        </CartPACMiniT>
                                                    }
                                                    {!this.props.isMini &&
                                                        <CartPACMiniF
                                                            bgc_value={values?.value}
                                                        >
                                                        </CartPACMiniF>
                                                    }
                                                </span>
                                            )
                                        }
                                    </div>
                                </div>
                            )}
                    </span>
                    <span className='ci_m_2'>
                        <div className='ci_m_2_counter'>
                            <button onClick={this.increaseProductCount}>
                                <img src={AddSign} alt='+' />
                            </button>
                            <p>{this.props.cart_info?.quantity}</p>
                            <button onClick={this.decreaseProductCount} className='ci_m_2_c_b'>
                                <img src={SubtractSign} alt='-' />
                            </button>
                        </div>
                        <div className='ci_m_2_image'>
                            {!this.props.isMini && this.props.cart_info?.gallery?.length > 1 &&
                                <button className='ci_m_2_image_al'
                                    onClick={this.decrementGalleryIndex}
                                >
                                    <img src={ArrowLeft} alt='L' />
                                </button>
                            }
                            {!this.props.isMini && this.props.cart_info?.gallery?.length > 1 &&
                                <button className=''
                                    onClick={this.incrementGalleryIndex}
                                >
                                    <img src={ArrowLeft} alt='R' />
                                </button>
                            }
                            <img src={resolveImageUrl(this.props.isMini ?
                                this.props.cart_info?.gallery[0] :
                                this.props.cart_info?.gallery[this.state.gallery_index])} alt='product'
                                className='ci_m_2_i_img'
                            />
                        </div>
                    </span>
                </div>
                <div className='ci_m_oof_btn_rmv'>
                    {!this.props.isMini &&
                        <p className='ci_m_p_subt'>Sub-Total: <span>{this.props.AllCurrencies?.[this.props.CurrentCurrency]?.symbol || '$'}{this.handleSubTotalCalc()}</span></p>
                    }
                    {!this.props.isMini && !this.props.cart_info?.inStock &&
                        <p className='ci_m_p_oof'>OUT OF STOCK</p>
                    }
                    <button className='ci_m_btn_rmv' onClick={this.handle_Remove_Cart_Item}>
                        REMOVE
                    </button>
                </div>
            </section>
        )
    }
}

const mapStateToProps = (state) => {
    return {
        CurrentCurrency: state.CurrentCurrency,
        AllCurrencies: state.AllCurrencies,
        UserCarts: state.UserCarts
    }
}

const mapDispatchToProps = (dispatch) => {
    return {
        UpdateUserCart: (index, data) => dispatch({ type: "UPDATE_USER_CARTS", product_index: index, product_data: data }),
        RemoveCartItem: (item_index) => dispatch({ type: "REMOVE_USER_CART_ITEM", payload: item_index })
    }
}

export default connect(mapStateToProps, mapDispatchToProps)(CartItem);
