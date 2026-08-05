import React, { Component } from 'react';
import './CurrencySwitcher.scss';
import { connect } from 'react-redux';
import { back_end_endpoint } from '../../Configs/BackEndEndpoint';

class CurrencySwitcher extends Component {

    getdata = async () => {
        await fetch(back_end_endpoint() + "/api/currencies")
            .catch(error => console.error(error))
            .then(async res => {
                const json_data = await res.json();
                this.props.setAllCurrencies(json_data);
            });
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
