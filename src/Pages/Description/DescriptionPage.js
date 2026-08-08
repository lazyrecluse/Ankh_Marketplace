import React, { Component } from 'react';
import './DescriptionPage.scss';
import { withRouter } from 'react-router-dom';
import { connect } from 'react-redux';
import parse from "html-react-parser";
import styled from 'styled-components';
import Alert from '../../Components/Alert/Alert';
import { getProduct } from '../../Api/catalog';

class DescriptionPage extends Component {

    constructor(props) {
        super(props)

        this.state = {
            productAttribs: {},
            galleryIndex: 0,
            ViewMoreDesc: false,
            openAlert: false,
            alertType: 1
        }
    }

    compareJSObjects = (Object_1, Object_2) => {
        const Object_1_Length = Object.keys(Object_1).length;
        const Object_2_Length = Object.keys(Object_2).length;

        if (Object_1_Length === Object_2_Length) {
            return Object.keys(Object_1).every(key => Object_2.hasOwnProperty(key) && Object_2[key] === Object_1[key]);
        } else {
            return false;
        }
    }

    getdata = async () => {
        try {
            const json_data = await getProduct(this.props.match?.params?.id);
            if (json_data?.attributes?.length > 0) {
                for (let i = 0; i < json_data?.attributes?.length; i++) {
                    const a_id = json_data?.attributes[i]?.id;
                    const a_val = json_data?.attributes[i]?.items[0]?.value;
                    let prev_state = this.state.productAttribs;
                    prev_state[a_id] = a_val;
                    this.setState({ productAttribs: { ...prev_state } });
                }
            }
            this.props.SetCurrentProduct(json_data);
        } catch (error) {
            console.error(error);
        }
    }

    setProductAttributes = (attrib_name, attrib_value) => {
        let prevState = this.state.productAttribs;
        prevState[attrib_name] = attrib_value;
        this.setState({ productAttribs: { ...prevState } });
    }

    handlePriceBasedOnCurr = () => {
        if (this.props.CurrentProduct?.prices?.length > 0) {
            const current_currency_symbol = this.props.AllCurrencies[this.props.CurrentCurrency]?.symbol || "$";
            const currency_obj = this.props.CurrentProduct?.prices?.filter(item => item?.currency?.symbol === current_currency_symbol);
            const amt = currency_obj[0]?.amount;
            if (amt !== undefined && amt !== null) return amt;
            const firstPrice = this.props.CurrentProduct?.prices[0]?.amount;
            return firstPrice !== undefined ? firstPrice : '';
        }
        return '';
    }

    AddtoCart = () => {
        let CartItem = {};

        CartItem["id"] = this.props.CurrentProduct?.id;
        CartItem["brand"] = this.props.CurrentProduct?.brand;
        CartItem["name"] = this.props.CurrentProduct?.name;
        CartItem["gallery"] = this.props.CurrentProduct?.gallery;
        CartItem["prices"] = this.props.CurrentProduct?.prices;
        CartItem["inStock"] = this.props.CurrentProduct?.inStock;
        CartItem["attributes"] = this.props.CurrentProduct?.attributes;
        CartItem["quantity"] = 1;

        if (this.props.CurrentProduct?.attributes?.length > 0) {
            for (let i = 0; i < this.props.CurrentProduct?.attributes?.length; i++) {
                CartItem[this.props.CurrentProduct?.attributes[i]?.id] = this.state.productAttribs[this.props.CurrentProduct?.attributes[i]?.id] === undefined ?
                    this.props.CurrentProduct?.attributes[i]?.items[0]?.value :
                    this.state.productAttribs[this.props.CurrentProduct?.attributes[i]?.id];
            }
            this.props.AddtoUserCart(CartItem);
        } else {
            this.props.AddtoUserCart(CartItem);
        }
    }

    handleAddtoCart = () => {
        if (this.props.CurrentProduct?.inStock) {
            if (this.props.UserCarts?.length > 0) {

                if (this.props.CurrentProduct?.attributes?.length > 0) {
                    // Checks if the Product exists
                    const productWithAttribs = this.props.UserCarts?.filter(item => item?.id === this.props.CurrentProduct?.id);
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
                            if (this.compareJSObjects({ ...CartProductAttrib }, { ...this.state.productAttribs })) {
                                ProductInCart = true;
                            }
                        }

                        // If the Product does not exist, add to cart
                        if (ProductInCart) {
                            this.setState({ alertType: 2, openAlert: true });
                        } else {
                            this.AddtoCart();
                        }

                    } else {
                        this.AddtoCart();
                    }
                } else {
                    // Checks if the Product exists
                    const productsWithoutAttribs = this.props.UserCarts?.filter(item => item?.id === this.props.CurrentProduct?.id);
                    // If the Product does not exist, add to cart
                    if (productsWithoutAttribs?.length > 0) {
                        this.setState({ alertType: 1, openAlert: true });
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

    alertStructure = () => {
        switch (this.state.alertType) {
            case 1:
                return {
                    heading: "This Product is available in your Cart!",
                    sub_heading: "What would you like to do?",
                    actions: [
                        {
                            name: "View Cart",
                            handleFunc: () => {
                                this.props.history?.push(`/carts`);
                                this.setState({ openAlert: false });
                            }
                        },
                        {
                            name: "Cancel",
                            handleFunc: () => {
                                this.setState({ openAlert: false });
                            }
                        }
                    ]
                }
            case 2:
                return {
                    heading: "This Product is available in your Cart with the current Attributes selected!",
                    sub_heading: "What would you like to do?",
                    actions: [
                        {
                            name: "View Cart",
                            handleFunc: () => {
                                this.props.history?.push(`/carts`);
                                this.setState({ openAlert: false });
                            }
                        },
                        {
                            name: "Cancel",
                            handleFunc: () => {
                                this.setState({ openAlert: false });
                            }
                        }
                    ]
                }
            default:
                return;
        }
    }

    componentDidMount = () => {
        document.title = 'ScandiStore | Description';
        this.props.ClearCurrentProduct();
        this.setState({ productAttribs: {} });
        this.getdata();
        window.scrollTo(0, 0);
    }

    render() {
        const DescPAC = styled.div`
            background: ${props => props.bgc_value};
            width: 32px;
            min-width: 32px;
            height: 32px;
            min-height: 32px;
        `;

        return (
            <main
                className='descpage_main'
                onClick={this.props.handle_CloseCartOrCurr}
            >
                {this.state.openAlert && <Alert structure={this.alertStructure()} />}
                {this.props.CurrentProduct &&
                    <div className='dp_m_w'>
                        <div className='dp_m_1'>
                            <div className='dp_m_1_ia'>
                                {this.props.CurrentProduct?.gallery?.length > 0 &&
                                    this.props.CurrentProduct?.gallery?.map((item, i) =>
                                        <img
                                            key={i}
                                            src={item}
                                            alt='prev'
                                            onClick={() => this.setState({ galleryIndex: i })}
                                        />
                                    )
                                }
                            </div>
                            {this.props.CurrentProduct?.gallery?.length > 0 &&
                                <img
                                    className='dp_m_1_ci'
                                    src={this.props.CurrentProduct?.gallery[this.state.galleryIndex]}
                                    alt='product_image' />
                            }
                        </div>
                        <div className='dp_m_2'>
                            <h1 className='dp_m_2_b'>{this.props.CurrentProduct?.brand}</h1>
                            <p className='dp_m_2_n'>{this.props.CurrentProduct?.name}</p>
                            {this.props.CurrentProduct?.attributes?.length > 0 &&
                                this.props.CurrentProduct?.attributes?.map((item, i) =>
                                    <div key={i} className='dp_m_1_a_w'>
                                        <p className='dp_m_2_p'>{`${item?.name}:`}</p>
                                        <div className='dp_m_1_a_w_b'>
                                            {item?.type === "text" &&
                                                item?.items?.length > 0 &&
                                                item?.items?.map((values, index) =>
                                                    <h3
                                                        key={index}
                                                        id={values?.value === this.state.productAttribs?.[item?.id] ? 'h3' : ''}
                                                        onClick={() => this.setProductAttributes(item?.id, values?.value)}
                                                    >{values?.value}</h3>
                                                )
                                            }
                                            {item?.type === "swatch" &&
                                                item?.items?.length > 0 &&
                                                item?.items?.map((values, index) =>
                                                    <span
                                                        key={index}
                                                        id={values?.value === this.state.productAttribs?.[item?.id] ? 'span' : ''}
                                                        onClick={() => this.setProductAttributes(item?.id, values?.value)}
                                                    >
                                                        <DescPAC
                                                            bgc_value={values?.value}
                                                        ></DescPAC>
                                                    </span>
                                                )
                                            }
                                        </div>
                                    </div>
                                )}
                            <p className='dp_m_2_p'>PRICE:</p>
                            <p className='dp_m_2_c'>{`${this.props.AllCurrencies?.length > 0 ? this.props.AllCurrencies[this.props.CurrentCurrency]?.symbol : ''}${this.handlePriceBasedOnCurr() === undefined ? '' : this.handlePriceBasedOnCurr()}`}</p>
                            <button
                                disabled={!this.props.CurrentProduct?.inStock}
                                onClick={this.handleAddtoCart}
                                className='dp_m_2_btn'
                            >
                                {!this.props.CurrentProduct?.inStock ?
                                    `OUT OF STOCK` :
                                    `ADD TO CART`
                                }</button>
                            <div className='dp_m_2_desc'>
                                {this.props.CurrentProduct?.description?.length > 200 ?
                                    parse(`${this.state.ViewMoreDesc ?
                                        this.props.CurrentProduct?.description :
                                        this.props.CurrentProduct?.description?.slice(0, 200)}
                                ${this.state.ViewMoreDesc ? '' : '...'}`) :
                                    parse(`${this.props.CurrentProduct?.description === undefined ? '<p></p>' : this.props.CurrentProduct?.description}`)
                                }
                            </div>
                            {this.props.CurrentProduct?.description?.length > 200 &&
                                <button
                                    className='dp_m_2_btn_vm'
                                    onClick={() => this.setState({ ViewMoreDesc: !this.state.ViewMoreDesc })}
                                >View {this.state.ViewMoreDesc ? 'Less' : 'More'}</button>
                            }
                        </div>
                    </div>
                }
                {!this.props.CurrentProduct &&
                    <p className='dp_m_loading'>Loading Product Description...</p>
                }
            </main>
        )
    }
}

const mapStateToProps = (state) => {
    return {
        AllCategories: state.AllCategories,
        CurrentCategory: state.CurrentCategory,
        UserCarts: state.UserCarts,
        AllCurrencies: state.AllCurrencies,
        CurrentCurrency: state.CurrentCurrency,
        CurrentProduct: state.CurrentProduct
    }
}

const mapDispatchToProps = (dispatch) => {
    return {
        AddtoUserCart: (item) => dispatch({ type: "ADD_USER_CARTS", payload: item }),
        ClearCurrentProduct: () => dispatch({ type: "CLEAR_CURRENT_PRODUCT" }),
        SetCurrentProduct: (product) => dispatch({ type: "SET_CURRENT_PRODUCT", payload: product })
    }
}

export default withRouter(connect(mapStateToProps, mapDispatchToProps)(DescriptionPage));
