import {
  combineReducers,
  configureStore,
  StateFromReducersMapObject,
} from "@reduxjs/toolkit";
import { setupListeners } from "@reduxjs/toolkit/query/react";
import {
  FLUSH,
  PAUSE,
  PERSIST,
  persistReducer,
  persistStore,
  PURGE,
  REGISTER,
  REHYDRATE,
} from "redux-persist";
import createWebStorage from "redux-persist/lib/storage/createWebStorage";

import { baseApi } from "~/features/common/api.slice";
import { configSlice } from "~/features/common/config.slice";
import { propertySlice } from "~/features/common/property.slice";
import { settingsSlice } from "~/features/common/settings.slice";
import { stylesSlice } from "~/features/common/styles.slice";
import { consentSlice } from "~/features/consent/consent.slice";

/**
 * To prevent the "redux-persist failed to create sync storage. falling back to noop storage"
 * console message within Next.js, the following snippet is required.
 * https://mightycoders.xyz/redux-persist-failed-to-create-sync-storage-falling-back-to-noop-storage
 */
const createNoopStorage = () => ({
  getItem() {
    return Promise.resolve(null);
  },
  setItem(_key: any, value: any) {
    return Promise.resolve(value);
  },
  removeItem() {
    return Promise.resolve();
  },
});

const storage =
  typeof window !== "undefined"
    ? createWebStorage("local")
    : createNoopStorage();

const reducer = {
  [baseApi.reducerPath]: baseApi.reducer,
  [configSlice.name]: configSlice.reducer,
  [consentSlice.name]: consentSlice.reducer,
  [settingsSlice.name]: settingsSlice.reducer,
  [stylesSlice.name]: stylesSlice.reducer,
  [propertySlice.name]: propertySlice.reducer,
};

export type RootState = StateFromReducersMapObject<typeof reducer>;

const allReducers = combineReducers(reducer);

const persistConfig = {
  key: "root",
  storage,

  /**
   * NOTE: Only persist the consent slice, since we want to remember the user's preferences across
   * refreshes. We don't persist other slices intentionally - especially the baseApi RTK slice, since
   * it's cache will persist and leave us with phantom subscriptions to non-existant components!
   */
  whitelist: [consentSlice.name],
};

const persistedReducer = persistReducer(persistConfig, allReducers);

export const makeStore = (
  preloadedState?: Parameters<typeof persistedReducer>[0],
) => {
  const store = configureStore({
    reducer: persistedReducer,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: {
          ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
        },
      }).concat(baseApi.middleware),
    preloadedState,
    devTools: true,
  });

  setupListeners(store.dispatch);

  return store;
};

const store = makeStore();

// The store is exposed on the window object when running in the Cypress test
// environment. This enables the custom `cy.dispatch` command.
if (typeof window !== "undefined" && window.Cypress) {
  window.store = store;
}

export default store;
export type AppStore = ReturnType<typeof makeStore>;
export type AppDispatch = AppStore["dispatch"];
export const persistor = persistStore(store);
