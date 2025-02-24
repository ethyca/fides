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

import { STORAGE_ROOT_KEY } from "~/constants";
import { authSlice } from "~/features/auth";
import { baseApi } from "~/features/common/api.slice";
import { featuresSlice } from "~/features/common/features";
import { healthApi } from "~/features/common/health.slice";
import { dirtyFormsSlice } from "~/features/common/hooks/dirty-forms.slice";
import { configWizardSlice } from "~/features/config-wizard/config-wizard.slice";
import { connectionTypeSlice } from "~/features/connection-type";
import { discoveryDetectionSlice } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { dataSubjectsSlice } from "~/features/data-subjects/data-subject.slice";
import { dataUseSlice } from "~/features/data-use/data-use.slice";
import { datamapSlice } from "~/features/datamap";
import { datasetSlice } from "~/features/dataset";
import { datastoreConnectionSlice } from "~/features/datastore-connections";
import { locationsSlice } from "~/features/locations/locations.slice";
import { organizationSlice } from "~/features/organization";
import { languageSlice } from "~/features/privacy-experience/language.slice";
import { privacyExperienceConfigSlice } from "~/features/privacy-experience/privacy-experience.slice";
import { privacyNoticesSlice } from "~/features/privacy-notices/privacy-notices.slice";
import { subjectRequestsSlice } from "~/features/privacy-requests";
import { propertySlice } from "~/features/properties";
import { systemSlice } from "~/features/system";
import { dictSuggestionsSlice } from "~/features/system/dictionary-form/dict-suggestion.slice";
import { taxonomySlice } from "~/features/taxonomy";
import { datasetTestSlice } from "~/features/test-datasets";
import { userManagementSlice } from "~/features/user-management";

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
  [authSlice.name]: authSlice.reducer,
  [configWizardSlice.name]: configWizardSlice.reducer,
  [connectionTypeSlice.name]: connectionTypeSlice.reducer,
  [dataSubjectsSlice.name]: dataSubjectsSlice.reducer,
  [dataUseSlice.name]: dataUseSlice.reducer,
  [datasetSlice.name]: datasetSlice.reducer,
  [datasetTestSlice.name]: datasetTestSlice.reducer,
  [datastoreConnectionSlice.name]: datastoreConnectionSlice.reducer,
  [discoveryDetectionSlice.name]: discoveryDetectionSlice.reducer,
  [featuresSlice.name]: featuresSlice.reducer,
  [languageSlice.name]: languageSlice.reducer,
  [locationsSlice.name]: locationsSlice.reducer,
  [organizationSlice.name]: organizationSlice.reducer,
  [privacyNoticesSlice.name]: privacyNoticesSlice.reducer,
  [privacyExperienceConfigSlice.name]: privacyExperienceConfigSlice.reducer,
  [propertySlice.name]: propertySlice.reducer,
  [subjectRequestsSlice.name]: subjectRequestsSlice.reducer,
  [systemSlice.name]: systemSlice.reducer,
  [taxonomySlice.name]: taxonomySlice.reducer,
  [userManagementSlice.name]: userManagementSlice.reducer,
  [dictSuggestionsSlice.name]: dictSuggestionsSlice.reducer,
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
    baseApi.reducerPath,
    healthApi.reducerPath,
    dictSuggestionsSlice.name,
  ],
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const makeStore = (
  preloadedState?: Parameters<typeof persistedReducer>[0],
) =>
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
