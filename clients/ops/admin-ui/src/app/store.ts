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

import { STORAGE_ROOT_KEY } from "../constants";
import { authApi, AuthState, reducer as authReducer } from "../features/auth";
import {
  connectionTypeApi,
  reducer as connectionTypeReducer,
} from "../features/connection-type";
import {
  datastoreConnectionApi,
  reducer as datastoreConnectionReducer,
} from "../features/datastore-connections";
import {
  privacyRequestApi,
  reducer as privacyRequestsReducer,
} from "../features/privacy-requests";
import {
  reducer as userManagementReducer,
  userApi,
} from "../features/user-management";

/**
 * To prevent the "redux-perist failed to create sync storage. falling back to noop storage"
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

const reducerMap = {
  [authApi.reducerPath]: authApi.reducer,
  auth: authReducer,
  [connectionTypeApi.reducerPath]: connectionTypeApi.reducer,
  connectionType: connectionTypeReducer,
  [datastoreConnectionApi.reducerPath]: datastoreConnectionApi.reducer,
  datastoreConnections: datastoreConnectionReducer,
  [privacyRequestApi.reducerPath]: privacyRequestApi.reducer,
  subjectRequests: privacyRequestsReducer,
  [userApi.reducerPath]: userApi.reducer,
  userManagement: userManagementReducer,
};

const allReducers = combineReducers(reducerMap);

const rootReducer = (state: any, action: AnyAction) => {
  let newState = { ...state };
  if (action.type === "auth/logout") {
    storage.removeItem(STORAGE_ROOT_KEY);
    newState = undefined;
  }
  return allReducers(newState, action);
};

const persistConfig = {
  key: "root",
  storage,
  /*
    NOTE: It is also strongly recommended to blacklist any api(s) that you have configured with RTK Query.
    If the api slice reducer is not blacklisted, the api cache will be automatically persisted 
    and restored which could leave you with phantom subscriptions from components that do not exist any more.
    (https://redux-toolkit.js.org/usage/usage-guide#use-with-redux-persist)
  */
  blacklist: [
    authApi.reducerPath,
    connectionTypeApi.reducerPath,
    datastoreConnectionApi.reducerPath,
    privacyRequestApi.reducerPath,
    userApi.reducerPath,
  ],
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export type RootState = StateFromReducersMapObject<typeof reducerMap>;

export const makeStore = (preloadedState?: Partial<RootState>) =>
  configureStore({
    reducer: persistedReducer,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: {
          ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
        },
      }).concat(
        privacyRequestApi.middleware,
        userApi.middleware,
        authApi.middleware,
        datastoreConnectionApi.middleware,
        connectionTypeApi.middleware
      ),
    devTools: true,
    preloadedState,
  });

let storedAuthState: AuthState | undefined;
if (typeof window !== "undefined" && "localStorage" in window) {
  const storedAuthStateString = localStorage.getItem(STORAGE_ROOT_KEY);
  if (storedAuthStateString) {
    try {
      storedAuthState = JSON.parse(storedAuthStateString);
    } catch (error) {
      // TODO: build in formal error logging system
      // eslint-disable-next-line no-console
      console.error(error);
    }
  }
}

const store = makeStore({
  auth: storedAuthState,
});

export const persistor = persistStore(store);

setupListeners(store.dispatch);

export default store;
