import rootReducer from "../Redux/index";
import { configureStore } from '@reduxjs/toolkit';
import { persistStore, persistReducer } from 'redux-persist';
import storage from 'redux-persist/lib/storage';
import { getUser, registerSessionClearCallback } from '../Auth/session';
import { loadCartFromStorage, saveCartToStorage } from '../Utils/cartStorage';

// UserCarts is blacklisted from global scandiweb-store to prevent
// carts from leaking across different user accounts.
const persistConfig = {
    key: 'scandiweb-store',
    storage,
    blacklist: ['UserCarts'],
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

const currentUser = getUser();
const initialCart = loadCartFromStorage(currentUser?.id);

const store = configureStore({
    reducer: persistedReducer,
    preloadedState: {
        UserCarts: initialCart,
    },
    middleware: (getDefaultMiddleware) =>
        getDefaultMiddleware({
            serializableCheck: false,
        }),
});

// Automatically save cart changes to the current user's scope (or guest scope)
let prevUserCarts = store.getState().UserCarts;
store.subscribe(() => {
    const state = store.getState();
    if (state.UserCarts !== prevUserCarts) {
        prevUserCarts = state.UserCarts;
        const user = getUser();
        saveCartToStorage(user?.id, state.UserCarts);
    }
});

// When session is cleared (logout), clear Redux cart so next user starts fresh
registerSessionClearCallback(() => {
    store.dispatch({ type: 'SET_USER_CARTS', payload: [] });
});

const persistedStore = persistStore(store);

export default store;
export { persistedStore };
