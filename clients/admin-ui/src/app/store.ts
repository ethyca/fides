import {
  AnyAction,
  combineReducers,
  configureStore,
  StateFromReducersMapObject,
} from "@reduxjs/toolkit";
import { setupListeners } from "@reduxjs/toolkit/query/react";
import {
  connectionTypeApi,
  reducer as connectionTypeReducer,
} from "connection-type/index";
import { reducer as datastoreConnectionReducer } from "datastore-connections/index";
import {
  privacyRequestApi,
  reducer as privacyRequestsReducer,
} from "privacy-requests/index";
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
import {
  reducer as userManagementReducer,
  userApi,
} from "user-management/index";

import { STORAGE_ROOT_KEY } from "~/constants";
import { baseApi } from "~/features/common/api.slice";
import { reducer as featuresReducer } from "~/features/common/features";
import { healthApi } from "~/features/common/health.slice";
import { dirtyFormsSlice } from "~/features/common/hooks/dirty-forms.slice";
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
import { datamapSlice } from "~/features/datamap";
import { reducer as datasetReducer } from "~/features/dataset";
import {
  organizationApi,
  reducer as organizationReducer,
} from "~/features/organization";
import { plusApi } from "~/features/plus/plus.slice";
import { reducer as systemReducer, systemApi } from "~/features/system";
import { reducer as taxonomyReducer, taxonomyApi } from "~/features/taxonomy";

import { authApi, reducer as authReducer } from "../features/auth";

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
  [authApi.reducerPath]: authApi.reducer,
  [baseApi.reducerPath]: baseApi.reducer,
  [connectionTypeApi.reducerPath]: connectionTypeApi.reducer,
  [datamapSlice.name]: datamapSlice.reducer,
  [dataQualifierApi.reducerPath]: dataQualifierApi.reducer,
  [dataSubjectsApi.reducerPath]: dataSubjectsApi.reducer,
  [dataUseApi.reducerPath]: dataUseApi.reducer,
  [dirtyFormsSlice.name]: dirtyFormsSlice.reducer,
  [healthApi.reducerPath]: healthApi.reducer,
  [organizationApi.reducerPath]: organizationApi.reducer,
  [plusApi.reducerPath]: plusApi.reducer,
  [privacyRequestApi.reducerPath]: privacyRequestApi.reducer,
  [scannerApi.reducerPath]: scannerApi.reducer,
  [systemApi.reducerPath]: systemApi.reducer,
  [taxonomyApi.reducerPath]: taxonomyApi.reducer,
  [userApi.reducerPath]: userApi.reducer,
  auth: authReducer,
  configWizard: configWizardReducer,
  connectionType: connectionTypeReducer,
  dataQualifier: dataQualifierReducer,
  dataSubjects: dataSubjectsReducer,
  dataUse: dataUseReducer,
  dataset: datasetReducer,
  datastoreConnections: datastoreConnectionReducer,
  features: featuresReducer,
  organization: organizationReducer,
  subjectRequests: privacyRequestsReducer,
  system: systemReducer,
  taxonomy: taxonomyReducer,
  userManagement: userManagementReducer,
};

export type RootState = StateFromReducersMapObject<typeof reducer>;

const allReducers = combineReducers(reducer);

const rootReducer = (state: RootState | undefined, action: AnyAction) => {
  let newState = state;
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
    baseApi.reducerPath,
    connectionTypeApi.reducerPath,
    dataQualifierApi.reducerPath,
    dataSubjectsApi.reducerPath,
    dataUseApi.reducerPath,
    healthApi.reducerPath,
    organizationApi.reducerPath,
    plusApi.reducerPath,
    privacyRequestApi.reducerPath,
    scannerApi.reducerPath,
    systemApi.reducerPath,
    taxonomyApi.reducerPath,
    userApi.reducerPath,
    dirtyFormsSlice.name,
  ],
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const makeStore = (preloadedState?: Partial<RootState>) =>
  configureStore({
    reducer: persistedReducer,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware({
        serializableCheck: {
          ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER],
        },
      }).concat(
        authApi.middleware,
        baseApi.middleware,
        connectionTypeApi.middleware,
        dataQualifierApi.middleware,
        dataSubjectsApi.middleware,
        dataUseApi.middleware,
        healthApi.middleware,
        organizationApi.middleware,
        plusApi.middleware,
        privacyRequestApi.middleware,
        scannerApi.middleware,
        systemApi.middleware,
        taxonomyApi.middleware,
        userApi.middleware
      ),
    devTools: true,
    preloadedState,
  });

const store = makeStore();

type AppStore = ReturnType<typeof makeStore>;
export type AppDispatch = AppStore["dispatch"];

export const persistor = persistStore(store);

setupListeners(store.dispatch);

export default store;
