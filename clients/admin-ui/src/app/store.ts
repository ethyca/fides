import {
  AnyAction,
  combineReducers,
  configureStore,
  StateFromReducersMapObject,
} from "@reduxjs/toolkit";
import { setupListeners } from "@reduxjs/toolkit/query/react";
import { reducer as connectionTypeReducer } from "connection-type/index";
import { reducer as datastoreConnectionReducer } from "datastore-connections/index";
import { reducer as privacyRequestsReducer } from "privacy-requests/index";
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
import { reducer as userManagementReducer } from "user-management/index";

import { STORAGE_ROOT_KEY } from "~/constants";
import { reducer as authReducer } from "~/features/auth";
import { baseApi } from "~/features/common/api.slice";
import { reducer as featuresReducer } from "~/features/common/features";
import { healthApi } from "~/features/common/health.slice";
import { dirtyFormsSlice } from "~/features/common/hooks/dirty-forms.slice";
import { reducer as configWizardReducer } from "~/features/config-wizard/config-wizard.slice";
import { reducer as dataQualifierReducer } from "~/features/data-qualifier/data-qualifier.slice";
import { reducer as dataSubjectsReducer } from "~/features/data-subjects/data-subject.slice";
import { reducer as dataUseReducer } from "~/features/data-use/data-use.slice";
import { datamapSlice } from "~/features/datamap";
import { reducer as datasetReducer } from "~/features/dataset";
import { reducer as organizationReducer } from "~/features/organization";
import { reducer as privacyNoticesReducer } from "~/features/privacy-notices/privacy-notices.slice";
import { reducer as systemReducer } from "~/features/system";
import { reducer as taxonomyReducer } from "~/features/taxonomy";

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
  // API reducers
  [baseApi.reducerPath]: baseApi.reducer,
  [healthApi.reducerPath]: healthApi.reducer,

  // Slice reducers
  [datamapSlice.name]: datamapSlice.reducer,
  [dirtyFormsSlice.name]: dirtyFormsSlice.reducer,
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
  privacyNotices: privacyNoticesReducer,
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
  blacklist: [baseApi.reducerPath, healthApi.reducerPath],
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
      }).concat(baseApi.middleware, healthApi.middleware),
    devTools: true,
    preloadedState,
  });

const store = makeStore();

type AppStore = ReturnType<typeof makeStore>;
export type AppDispatch = AppStore["dispatch"];

export const persistor = persistStore(store);

setupListeners(store.dispatch);

export default store;
