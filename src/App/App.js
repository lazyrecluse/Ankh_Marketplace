import React, { Component } from 'react';
import './App.scss';
import { Switch, Route, Redirect } from 'react-router-dom';
import { connect } from 'react-redux';
import AppBar from '../Components/AppBar/AppBar';
import CategoryPage from '../Pages/Category/CategoryPage';
import DescriptionPage from '../Pages/Description/DescriptionPage';
import CartPage from '../Pages/Cart/CartPage';
import CheckoutPage from '../Pages/Checkout/CheckoutPage';
import MissingPage from '../Pages/Missing/MissingPage';
import AuthPage from '../Pages/Auth/AuthPage';
import BuyerOnboarding from '../Pages/Onboarding/BuyerOnboarding';
import SupplierOnboarding from '../Pages/Onboarding/SupplierOnboarding';
import BuyerDashboard from '../Pages/Dashboard/BuyerDashboard';
import SupplierDashboard from '../Pages/Dashboard/SupplierDashboard';
import AIAssistant from '../Components/AIAssistant/AIAssistant';

class App extends Component {
  constructor(props) {
    super(props)
    this.state = {
      openCurrSwitcher: false,
      openMiniCartOverlay: false
    }
  }

  setOpenCurrSwitcher = (state) => {
    this.setState({ openCurrSwitcher: state });
  }

  setOpenMiniCartOverlay = (state) => {
    this.setState({ openMiniCartOverlay: state });
  }

  handle_CloseCartOrCurr = () => {
    if (this.state.openCurrSwitcher) {
      this.setState({ openCurrSwitcher: false });
    }
    if (this.state.openMiniCartOverlay) {
      this.setState({ openMiniCartOverlay: false });
    }
  }

  total_no_of_cart_items = () => {
    if (this.props.UserCarts?.length > 0) {
      let temp_total = 0;
      for (let i = 0; i < this.props.UserCarts?.length; i++) {
        temp_total += parseInt(this.props.UserCarts[i]?.quantity);
      }
      this.props.setTotalCarts(temp_total);
    } else {
      this.props.setTotalCarts(0);
    }
  }

  total_cart_prices = () => {
    const current_currency = this.props.AllCurrencies[this.props.CurrentCurrency]?.symbol || "$";
    if (this.props.UserCarts?.length > 0) {
      let temp_total_price = 0;
      for (let i = 0; i < this.props.UserCarts?.length; i++) {
        const quantity = parseInt(this.props.UserCarts[i]?.quantity) || 1;
        const price_obj = this.props.UserCarts[i]?.prices?.filter(item => item?.currency?.symbol === current_currency);
        const price_val = price_obj?.[0]?.amount !== undefined ? price_obj[0].amount : (this.props.UserCarts[i]?.prices?.[0]?.amount || 0);
        const price = parseFloat(price_val);
        temp_total_price += parseFloat(price * quantity);
      }
      const stringify_total_price = temp_total_price.toString();
      const total_price_to_2dp = parseFloat(stringify_total_price).toFixed(2);
      this.props.setTotalCartsPrice(total_price_to_2dp);
    } else {
      this.props.setTotalCartsPrice("0.00");
    }
  }

  componentDidMount = () => {
    this.total_no_of_cart_items();
    this.total_cart_prices();
  }
  componentDidUpdate = (prevProps) => {
    if (prevProps.UserCarts !== this.props.UserCarts) {
      this.total_no_of_cart_items();
      this.total_cart_prices();
    }
    if (prevProps.CurrentCurrency !== this.props.CurrentCurrency) {
      this.total_cart_prices();
    }
  }

  render() {
    return (
      <div className='app_main'>
        <div
          className='app_m_fade'
          id={this.state.openMiniCartOverlay ? 'app_m_fade' : ''}
          onClick={this.handle_CloseCartOrCurr}
        ></div>
        <Route render={({ location }) => {
          const isAuthPage = location.pathname.startsWith('/login');
          return !isAuthPage ? (
            <AppBar
              openCurrSwitcher={this.state.openCurrSwitcher}
              openMiniCartOverlay={this.state.openMiniCartOverlay}
              setOpenCurrSwitcher={this.setOpenCurrSwitcher}
              setOpenMiniCartOverlay={this.setOpenMiniCartOverlay}
              handle_CloseCartOrCurr={this.handle_CloseCartOrCurr}
            />
          ) : null;
        }} />
        <AIAssistant />
        <div className='app_w'>
          <Switch>
            <Redirect exact={true} from="/" to="/products" />
            <Route exact path="/products">
              <CategoryPage
                handle_CloseCartOrCurr={this.handle_CloseCartOrCurr}
              />
            </Route>
            <Route path="/products/:id">
              <DescriptionPage
                handle_CloseCartOrCurr={this.handle_CloseCartOrCurr}
              />
            </Route>
            <Route path="/carts">
              <CartPage
                handle_CloseCartOrCurr={this.handle_CloseCartOrCurr}
              />
            </Route>
            <Route path="/checkout">
              <CheckoutPage
                handle_CloseCartOrCurr={this.handle_CloseCartOrCurr}
              />
            </Route>
            <Route exact path="/login/buyer">
              <AuthPage buyerMode={true} />
            </Route>
            <Route exact path="/login">
              <AuthPage />
            </Route>
            <Route path="/onboarding/buyer">
              <BuyerOnboarding />
            </Route>
            <Route path="/onboarding/supplier">
              <SupplierOnboarding />
            </Route>
            <Route path="/buyer/dashboard">
              <BuyerDashboard />
            </Route>
            <Route path="/supplier/dashboard">
              <SupplierDashboard />
            </Route>
            <Route path="*">
              <MissingPage
                handle_CloseCartOrCurr={this.handle_CloseCartOrCurr}
              />
            </Route>
          </Switch>
        </div>
      </div>
    )
  }
}

const mapStateToProps = (state) => {
  return {
    UserCarts: state.UserCarts,
    CurrentCurrency: state.CurrentCurrency,
    AllCurrencies: state.AllCurrencies
  }
}

const mapDispatchToProps = (dispatch) => {
  return {
    setTotalCarts: (total_carts) => dispatch({ type: 'SET_TOTAL_CARTS', payload: total_carts }),
    setTotalCartsPrice: (total_price) => dispatch({ type: 'SET_TOTAL_CARTS_PRICE', payload: total_price })
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(App);