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
} from "connection-type/index";
import {
  datastoreConnectionApi,
  reducer as datastoreConnectionReducer,
} from "datastore-connections/index";
import {
  privacyRequestApi,
  reducer as privacyRequestsReducer,
} from "privacy-requests/index";
import {
  reducer as userManagementReducer,
  userApi,
} from "user-management/index";

import { plusApi } from "~/features/common/plus.slice";
import { reducer as configWizardReducer } from "~/features/config-wizard/config-wizard.slice";
import { scannerApi } from "~/features/config-wizard/scanner.slice";
import {
  dataQualifierApi,
  reducer as dataQualifierReducer,
} from "~/features/data-qualifier/data-qualifier.slice";
import {
  dataSubjectsApi,
  reducer as dataSubjectsReducer,
} from "~/features/data-subjects/data-subject.slice";
import {
  dataUseApi,
  reducer as dataUseReducer,
} from "~/features/data-use/data-use.slice";
import { datasetApi, reducer as datasetReducer } from "~/features/dataset";
import {
  organizationApi,
  reducer as organizationReducer,
} from "~/features/organization";
import { reducer as systemReducer, systemApi } from "~/features/system";
import { reducer as taxonomyReducer, taxonomyApi } from "~/features/taxonomy";
import { reducer as userReducer } from "~/features/user";

// import { createWrapper } from "next-redux-wrapper";
import { STORED_CREDENTIALS_KEY } from "../constants";
import {
  authApi,
  AuthState,
  credentialStorage,
  reducer as authReducer,
} from "../features/auth";


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

const reducer = {
  [privacyRequestApi.reducerPath]: privacyRequestApi.reducer,
  subjectRequests: privacyRequestsReducer,
  [userApi.reducerPath]: userApi.reducer,
  [authApi.reducerPath]: authApi.reducer,
  userManagement: userManagementReducer,
  [datastoreConnectionApi.reducerPath]: datastoreConnectionApi.reducer,
  datastoreConnections: datastoreConnectionReducer,
  auth: authReducer,
  [connectionTypeApi.reducerPath]: connectionTypeApi.reducer,
  connectionType: connectionTypeReducer,
  configWizard: configWizardReducer,
  user: userReducer,
  dataset: datasetReducer,
  taxonomy: taxonomyReducer,
  dataQualifier: dataQualifierReducer,
  dataSubjects: dataSubjectsReducer,
  dataUse: dataUseReducer,
  organization: organizationReducer,
  system: systemReducer,
  [datasetApi.reducerPath]: datasetApi.reducer,
  [organizationApi.reducerPath]: organizationApi.reducer,
  [scannerApi.reducerPath]: scannerApi.reducer,
  [systemApi.reducerPath]: systemApi.reducer,
  [taxonomyApi.reducerPath]: taxonomyApi.reducer,
  [dataQualifierApi.reducerPath]: dataQualifierApi.reducer,
  [dataSubjectsApi.reducerPath]: dataSubjectsApi.reducer,
  [dataUseApi.reducerPath]: dataUseApi.reducer,
  [plusApi.reducerPath]: plusApi.reducer,
  [datastoreConnectionApi.reducerPath]: datastoreConnectionApi.reducer,
  datastoreConnections: datastoreConnectionReducer,
  [privacyRequestApi.reducerPath]: privacyRequestApi.reducer,
  subjectRequests: privacyRequestsReducer,
  [userApi.reducerPath]: userApi.reducer,
  userManagement: userManagementReducer,
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export type RootState = StateFromReducersMapObject<typeof reducer>;

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
        connectionTypeApi.middleware,
        datasetApi.middleware,
        organizationApi.middleware,
        scannerApi.middleware,
        systemApi.middleware,
        taxonomyApi.middleware,
        dataQualifierApi.middleware,
        dataSubjectsApi.middleware,
        dataUseApi.middleware,
        plusApi.middleware
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
// export const wrapper = createWrapper<AppStore>(makeStore);
