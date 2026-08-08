import React, { Component } from 'react';
import './CurrencySwitcher.scss';
import { connect } from 'react-redux';
import { getCurrencies } from '../../Api/catalog';

class CurrencySwitcher extends Component {

    getdata = async () => {
        try {
            this.props.setAllCurrencies(await getCurrencies());
        } catch (error) {
            console.error(error);
        }
    }

    componentDidMount = () => {
        this.getdata();
    }

    render() {
        return (
            <section className='currency_switcher_main'>
                {this.props.AllCurrencies?.length > 0 &&
                    this.props.AllCurrencies?.map((item, i) =>
                        <p
                            key={i}
                            className={this.props.CurrentCurrency === i ? 'currency' : ''}
                            onClick={() => {
                                this.props.setCurrentCurrency(i);
                                this.props.handle_CloseCartOrCurr();
                            }}
                        >
                            {`${item?.symbol} ${item?.label}`}
                        </p>
                    )}
            </section>
        )
    }
}

const mapStateToProps = (state) => {
    return {
        AllCurrencies: state.AllCurrencies,
        CurrentCurrency: state.CurrentCurrency
    }
}

const mapDispatchToProps = (dispatch) => {
    return {
        setAllCurrencies: (all_currencies) => dispatch({ type: "ALL_CURRENCIES", payload: all_currencies }),
        setCurrentCurrency: (current_currency) => dispatch({ type: "CURRENT_CURRENCY", payload: current_currency })
    }
}

export default (connect(mapStateToProps, mapDispatchToProps)(CurrencySwitcher));
