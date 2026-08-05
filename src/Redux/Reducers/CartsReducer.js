export const total_carts = (state = 0, action) => {
    switch (action.type) {
        case "SET_TOTAL_CARTS":
            return action.payload;
        default:
            return state;
    }
}

export const total_cart_tax = (state = 0, action) => {
    switch (action.type) {
        case "SET_TOTAL_CARTS_TAX":
            return action.payload;
        default:
            return state;
    }
}

export const total_carts_price = (state = "0.00", action) => {
    switch (action.type) {
        case "SET_TOTAL_CARTS_PRICE":
            return action.payload;
        default:
            return state;
    }
}

export const user_carts = (state = [], action) => {
    switch (action.type) {
        case "UPDATE_USER_CARTS":
            let state_update = state;
            state_update[action.product_index] = action.product_data;
            return [...state_update];
        case "REMOVE_USER_CART_ITEM":
            let state_remove = state;
            const new_state = state_remove.filter((item, index) => index !== action.payload);
            return new_state;
        case "ADD_USER_CARTS":
            return [action.payload, ...state];
        case "CLEAR_USER_CARTS":
            return [];
        default:
            return state;
    }
}