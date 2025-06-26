/**
 * External Store Configuration
 *
 * COPIED & ADAPTED FROM: clients/admin-ui/src/app/store.ts
 *
 * Key differences for external users:
 * - Simplified store structure (only auth and manual tasks)
 * - External-specific reducers and APIs
 * - Same redux-persist strategy as admin-ui
 * - Isolated from main privacy-center store
 *
 * IMPORTANT: When updating admin-ui store.ts, review this store for sync!
 */

import {
  AnyAction,
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
import { settingsSlice } from "~/features/common/settings.slice";

import { externalAuthSlice } from "./external-auth.slice";
import { externalManualTasksReducer } from "./external-manual-tasks.slice";

/**
 * To prevent the "redux-persist failed to create sync storage. falling back to noop storage"
 * console message within Next.js, the following snippet is required.
 * {@https://mightycoders.xyz/redux-persist-failed-to-create-sync-storage-falling-back-to-noop-storage}
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
  // API reducers
  [baseApi.reducerPath]: baseApi.reducer,

  // Slice reducers
  [externalAuthSlice.name]: externalAuthSlice.reducer,
  [settingsSlice.name]: settingsSlice.reducer,
  externalManualTasks: externalManualTasksReducer,
};

export type ExternalRootState = StateFromReducersMapObject<typeof reducer>;

const allReducers = combineReducers(reducer);
const rootReducer = (
  state: ExternalRootState | undefined,
  action: AnyAction,
) => {
  let newState = state;
  if (action.type === "externalAuth/logout") {
    storage.removeItem("external-manual-tasks:root");
    newState = undefined;
  }
  return allReducers(newState, action);
};

const persistConfig = {
  key: "external-manual-tasks:root",
  storage,
  /*
    NOTE: It is also strongly recommended to blacklist any api(s) that you have configured with RTK Query.
    If the api slice reducer is not blacklisted, the api cache will be automatically persisted
    and restored which could leave you with phantom subscriptions from components that do not exist any more.
    (https://redux-toolkit.js.org/usage/usage-guide#use-with-redux-persist)
  */
  blacklist: [baseApi.reducerPath],
};

export const persistedReducer = persistReducer(persistConfig, rootReducer);

export const makeExternalStore = (
  preloadedState?: Parameters<typeof persistedReducer>[0],
) =>
  configureStore({
    reducer: persistedReducer,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: {
          ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
        },
      }).concat(baseApi.middleware),
    devTools: true,
    preloadedState,
  });

const externalStore = makeExternalStore();

type ExternalStore = ReturnType<typeof makeExternalStore>;
export type ExternalDispatch = ExternalStore["dispatch"];

export const externalPersistor = persistStore(externalStore);

setupListeners(externalStore.dispatch);

export default externalStore;
