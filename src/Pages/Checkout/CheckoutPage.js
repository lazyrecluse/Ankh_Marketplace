import React, { Component } from 'react';
import { connect } from 'react-redux';
import { withRouter } from 'react-router-dom';
import { placeOrder } from '../../Api/orders';
import { isLoggedIn } from '../../Auth/session';
import './CheckoutPage.scss';

class CheckoutPage extends Component {
    constructor(props) {
        super(props);
        this.state = {
            shippingName: '',
            shippingAddress: '',
            shippingCity: '',
            shippingCountry: '',
            loading: false,
            error: '',
            success: false,
            orderId: null
        };
    }

    componentDidMount = () => {
        document.title = `ScandiStore | Checkout`;
        // Ensure user is signed in to check out
        if (!isLoggedIn()) {
            this.props.history.push('/login');
        }
    }

    handleInputChange = (e) => {
        this.setState({ [e.target.name]: e.target.value });
    }

    handlePlaceOrder = async (e) => {
        e.preventDefault();
        this.setState({ error: '', loading: true });

        const current_currency_symbol = this.props.AllCurrencies[this.props.CurrentCurrency]?.symbol || "$";

        // Build items
        const orderItems = this.props.UserCarts.map(item => {
            const priceObj = item.prices?.find(p => p.currency?.symbol === current_currency_symbol) || item.prices?.[0];
            return {
                product_id: item.id,
                quantity: parseInt(item.quantity),
                price_amount: parseFloat(priceObj?.amount || 0)
            };
        });

        const body = {
            shipping_name: this.state.shippingName,
            shipping_address: this.state.shippingAddress,
            shipping_city: this.state.shippingCity,
            shipping_country: this.state.shippingCountry,
            total_price: parseFloat(this.props.TotalCartsPrice),
            currency_symbol: current_currency_symbol,
            items: orderItems
        };

        try {
            const data = await placeOrder(body);
            this.setState({ success: true, orderId: data.order_id });
            this.props.clearCart();
        } catch (err) {
            this.setState({ error: err.message });
        } finally {
            this.setState({ loading: false });
        }
    }

    render() {
        const current_currency_symbol = this.props.AllCurrencies[this.props.CurrentCurrency]?.symbol || "$";

        if (this.state.success) {
            return (
                <div className="checkoutpage_main success-view">
                    <div className="card checkout-success-card">
                        <h2>🎉 Order Placed Successfully!</h2>
                        <p>Thank you for your business. Your B2B order reference is <strong>#{this.state.orderId}</strong>.</p>
                        <p className="text-muted">The supplier has been notified and will update your order status soon.</p>
                        <div className="success-actions">
                            <button className="btn-primary" onClick={() => this.props.history.push('/buyer/dashboard')}>
                                View Dashboard & Track Order
                            </button>
                            <button className="btn-secondary" onClick={() => this.props.history.push('/products')}>
                                Continue Browsing
                            </button>
                        </div>
                    </div>
                </div>
            );
        }

        return (
            <main className='checkoutpage_main' onClick={this.props.handle_CloseCartOrCurr}>
                <div className='cop_m_wrapper'>
                    <h1 className='cop_m_h'>CHECKOUT</h1>
                    
                    {this.state.error && <div className="checkout-alert error">{this.state.error}</div>}

                    {this.props.UserCarts.length === 0 ? (
                        <div className="card empty-checkout-card">
                            <p>Your shopping cart is empty. Add products to cart before checking out.</p>
                            <button className="btn-primary" onClick={() => this.props.history.push('/products')}>
                                Browse fabrics
                            </button>
                        </div>
                    ) : (
                        <div className="checkout-layout">
                            {/* Shipping Form */}
                            <form className="card checkout-form" onSubmit={this.handlePlaceOrder}>
                                <h3>Shipping & Delivery Information</h3>
                                <div className="form-group">
                                    <label>Recipient / Business Contact Name</label>
                                    <input 
                                        type="text" 
                                        name="shippingName" 
                                        required 
                                        placeholder="e.g. John Doe, Logistics Manager" 
                                        value={this.state.shippingName} 
                                        onChange={this.handleInputChange} 
                                    />
                                </div>
                                <div className="form-group">
                                    <label>Street Address</label>
                                    <input 
                                        type="text" 
                                        name="shippingAddress" 
                                        required 
                                        placeholder="e.g. 456 Industrial Parkway, Suite B" 
                                        value={this.state.shippingAddress} 
                                        onChange={this.handleInputChange} 
                                    />
                                </div>
                                <div className="onboard-grid">
                                    <div className="form-group">
                                        <label>City</label>
                                        <input 
                                            type="text" 
                                            name="shippingCity" 
                                            required 
                                            placeholder="e.g. Milan" 
                                            value={this.state.shippingCity} 
                                            onChange={this.handleInputChange} 
                                        />
                                    </div>
                                    <div className="form-group">
                                        <label>Country</label>
                                        <input 
                                            type="text" 
                                            name="shippingCountry" 
                                            required 
                                            placeholder="e.g. Italy" 
                                            value={this.state.shippingCountry} 
                                            onChange={this.handleInputChange} 
                                        />
                                    </div>
                                </div>
                                <button type="submit" className="btn-primary" disabled={this.state.loading}>
                                    {this.state.loading ? 'Placing Order...' : 'Confirm and Place Order'}
                                </button>
                            </form>

                            {/* Order Summary */}
                            <div className="card checkout-summary">
                                <h3>Order Summary</h3>
                                <div className="summary-items">
                                    {this.props.UserCarts.map((item, index) => {
                                        const priceObj = item.prices?.find(p => p.currency?.symbol === current_currency_symbol) || item.prices?.[0];
                                        return (
                                            <div key={index} className="summary-item">
                                                <div>
                                                    <p className="item-name">{item.name}</p>
                                                    <p className="item-qty text-muted">{item.brand} • Qty: {item.quantity}</p>
                                                </div>
                                                <span className="item-price">
                                                    {current_currency_symbol}{(parseFloat(priceObj?.amount || 0) * parseInt(item.quantity)).toFixed(2)}
                                                </span>
                                            </div>
                                        );
                                    })}
                                </div>
                                <div className="divider"></div>
                                <div className="summary-total">
                                    <span>Total Price (excl. VAT)</span>
                                    <span className="total-val">{current_currency_symbol}{this.props.TotalCartsPrice}</span>
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </main>
        );
    }
}

const mapStateToProps = (state) => {
    return {
        UserCarts: state.UserCarts,
        TotalCartsPrice: state.TotalCartsPrice,
        CurrentCurrency: state.CurrentCurrency,
        AllCurrencies: state.AllCurrencies
    };
};

const mapDispatchToProps = (dispatch) => {
    return {
        clearCart: () => {
            dispatch({ type: 'CLEAR_USER_CARTS' });
            dispatch({ type: 'SET_TOTAL_CARTS', payload: 0 });
            dispatch({ type: 'SET_TOTAL_CARTS_PRICE', payload: "0.00" });
        }
    };
};

export default connect(mapStateToProps, mapDispatchToProps)(withRouter(CheckoutPage));
