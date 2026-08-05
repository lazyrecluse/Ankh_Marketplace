import React, { Component } from 'react';
import './ProductCard.scss';
import CartIcon from '../../Images/CartWhite.svg';
import { withRouter } from 'react-router-dom';
import { connect } from 'react-redux';
import { back_end_endpoint } from '../../Configs/BackEndEndpoint';

class ProductCard extends Component {

    compareJSObjects = (Object_1, Object_2) => {
        const Object_1_Length = Object.keys(Object_1).length;
        const Object_2_Length = Object.keys(Object_2).length;

        if (Object_1_Length === Object_2_Length) {
            return Object.keys(Object_1).every(key => Object_2.hasOwnProperty(key) && Object_2[key] === Object_1[key]);
        } else {
            return false;
        }
    }

    handleOpenPDP = () => {
        this.props.history?.push(`/products/${this.props.product_info?.id}`);
    }

    handlePriceBasedOnCurr = () => {
        if (this.props.product_info?.prices?.length > 0) {
            const current_currency_symbol = this.props.AllCurrencies[this.props.CurrentCurrency]?.symbol || "$";
            const currency_obj = this.props.product_info?.prices.filter(item => item?.currency?.symbol === current_currency_symbol);
            const amt = currency_obj[0]?.amount;
            if (amt !== undefined && amt !== null) return amt;
            const firstPrice = this.props.product_info?.prices[0]?.amount;
            return firstPrice !== undefined ? firstPrice : '';
        }
        return '';
    }

    AddtoCart = () => {
        let CartItem = {};

        CartItem["id"] = this.props.product_info?.id;
        CartItem["brand"] = this.props.product_info?.brand;
        CartItem["name"] = this.props.product_info?.name;
        CartItem["gallery"] = this.props.product_info?.gallery;
        CartItem["prices"] = this.props.product_info?.prices;
        CartItem["inStock"] = this.props.product_info?.inStock;
        CartItem["attributes"] = this.props.product_info?.attributes;
        CartItem["quantity"] = 1;

        if (this.props.product_info?.attributes?.length > 0) {
            if (window.confirm('This Product contains Attributes, would you like the Default Attributes to be applied before adding to Cart?')) {
                for (let i = 0; i < this.props.product_info?.attributes?.length; i++) {
                    CartItem[this.props.product_info?.attributes[i]?.id] = this.props.product_info?.attributes[i]?.items[0]?.value;
                }
                this.props.AddtoUserCart(CartItem);
            } else {
                alert("Product was not added to Cart!!!");
            }
        } else {
            this.props.AddtoUserCart(CartItem);
        }
    }

    handleAddtoCart = () => {
        if (this.props.product_info?.inStock) {
            if (this.props.UserCarts?.length > 0) {

                if (this.props.product_info?.attributes?.length > 0) {

                    let CurrentProductAttrib = {};
                    for (let i = 0; i < this.props.product_info?.attributes?.length; i++) {
                        CurrentProductAttrib[this.props.product_info?.attributes[i]?.id] = this.props.product_info?.attributes[i]?.items[0]?.value
                    }

                    // Checks if the Product exists
                    const productWithAttribs = this.props.UserCarts?.filter(item => item?.id === this.props.product_info?.id);

                    // If the Product does not exist, add to cart
                    if (productWithAttribs?.length > 0) {
                        // set's Product with this Attribute to false
                        let ProductInCart = false;

                        // checks through the Products filtered
                        for (let i = 0; i < productWithAttribs?.length; i++) {
                            let CartProductAttrib = {};
                            // Generates comparable Attribute Object
                            for (let j = 0; j < productWithAttribs[i]?.attributes?.length; j++) {
                                CartProductAttrib[productWithAttribs[i]?.attributes[j]?.id] = productWithAttribs[i]?.[productWithAttribs[i]?.attributes[j]?.id];
                            }
                            // Compares Generated Attribute Object with the Current Attribute Object Selected in the Desc Page
                            if (this.compareJSObjects({ ...CartProductAttrib }, { ...CurrentProductAttrib })) {
                                ProductInCart = true;
                            }
                        }

                        // If the Product does not exist, add to cart
                        if (ProductInCart) {
                            if (window.confirm(`This Product is available in your Cart with the Default Attributes selected, would you like to view your Cart?`)) {
                                this.props.history?.push(`/carts`);
                            }
                        } else {
                            this.AddtoCart();
                        }
                    } else {
                        this.AddtoCart();
                    }

                } else {
                    // Checks if the Product exists
                    const productsWithoutAttribs = this.props.UserCarts?.filter(item => item?.id === this.props.product_info?.id);
                    // If the Product does not exist, add to cart
                    if (productsWithoutAttribs?.length > 0) {
                        if (window.confirm(`This Product is available in your Cart, would you like to view your Cart?`)) {
                            this.props.history?.push(`/carts`);
                        }
                    } else {
                        this.AddtoCart();
                    }
                }

            } else {
                this.AddtoCart();
            }
        } else {
            alert(`Product is OUT-OF-STOCK`);
        }
    }

    render() {
        return (
            <section className='productcard_main'>
                <div
                    className='pc_m_oos'
                    id={this.props.product_info?.inStock ? '' : 'pc_m_oos'}
                    onClick={this.handleOpenPDP}
                >
                    <p>OUT OF STOCK</p>
                </div>
                <div
                    className={this.props.product_info?.inStock ? 'pc_m_cart' : 'pc_m_cart_dn'}
                    onClick={this.handleAddtoCart}>
                    <img
                        src={CartIcon}
                        alt='add'
                    />
                </div>
                {this.props.product_info?.gallery[0] && (this.props.product_info?.gallery[0].includes("http") || this.props.product_info?.gallery[0].startsWith("/")) ?
                    <img
                        src={this.props.product_info?.gallery[0].startsWith('/') ? back_end_endpoint() + this.props.product_info?.gallery[0] : this.props.product_info?.gallery[0]}
                        alt='product'
                        className='pc_m_img'
                        id={this.props.product_info?.inStock ? '' : 'pc_m_img'}
                        onClick={this.handleOpenPDP}
                    /> : <div className='pc_m_img'></div>
                }
                <div className='pc_m_desc'>
                    <div
                        className='pc_m_ep'
                        onClick={this.handleOpenPDP}
                    ></div>
                    <p
                        className='pc_m_bname'
                        id={this.props.product_info?.inStock ? '' : 'pc_m_bname'}
                        onClick={this.handleOpenPDP}
                    >{`${this.props.product_info?.brand} ${this.props.product_info?.name}`}</p>
                    <p
                        className='pc_m_bname pc_m_price'
                        id={this.props.product_info?.inStock ? '' : 'pc_m_bname'}
                        onClick={this.handleOpenPDP}
                    >
                        {this.props.AllCurrencies?.length > 0 ?
                            this.props.AllCurrencies[this.props.CurrentCurrency]?.symbol : ''
                        }
                        {this.handlePriceBasedOnCurr() === undefined ? '' : this.handlePriceBasedOnCurr()}
                    </p>
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
        AddtoUserCart: (item) => dispatch({ type: "ADD_USER_CARTS", payload: item }),
    }
}

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(ProductCard));
