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
  PURGE,
  REGISTER,
  REHYDRATE,
} from "redux-persist";
import createWebStorage from "redux-persist/lib/storage/createWebStorage";

import { baseApi } from "~/features/common/api.slice";
import { reducer as configReducer } from "~/features/common/config.slice";
import { reducer as consentReducer } from "~/features/consent/consent.slice";

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
  config: configReducer,
  consent: consentReducer,
};

export type RootState = StateFromReducersMapObject<typeof reducer>;

const allReducers = combineReducers(reducer);

const persistConfig = {
  key: "root",
  storage,
  /*
   * NOTE: It is also strongly recommended to blacklist any api(s) that you have configured with RTK
   * Query. If the api slice reducer is not blacklisted, the api cache will be automatically
   * persisted and restored which could leave you with phantom subscriptions from components that do
   * not exist any more.
   * https://redux-toolkit.js.org/usage/usage-guide#use-with-redux-persist
   */
  blacklist: [
    "config", // don't persist the config store - this should always be refreshed from the server!
    baseApi.reducerPath,
  ],
};

const persistedReducer = persistReducer(persistConfig, allReducers);

// hello
export const makeStore = (preloadedState?: Partial<RootState>) => {
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

export type AppStore = ReturnType<typeof makeStore>;
export type AppDispatch = AppStore["dispatch"];
