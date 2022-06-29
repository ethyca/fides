import { configureStore } from "@reduxjs/toolkit";
import { setupListeners } from "@reduxjs/toolkit/query/react";
import { createWrapper } from "next-redux-wrapper";

import {
  organizationApi,
  reducer as organizationReducer,
} from "~/features/config-wizard/organization.slice";
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
import { systemApi } from "~/features/system";
import {
  dataCategoriesApi,
  reducer as dataCategoriesReducer,
} from "~/features/taxonomy";
import { reducer as userReducer } from "~/features/user";

const makeStore = () => {
  const store = configureStore({
    reducer: {
      user: userReducer,
      dataset: datasetReducer,
      dataCategories: dataCategoriesReducer,
      dataQualifier: dataQualifierReducer,
      dataSubjects: dataSubjectsReducer,
      dataUse: dataUseReducer,
      organization: organizationReducer,
      [datasetApi.reducerPath]: datasetApi.reducer,
      [organizationApi.reducerPath]: organizationApi.reducer,
      [scannerApi.reducerPath]: scannerApi.reducer,
      [systemApi.reducerPath]: systemApi.reducer,
      [dataCategoriesApi.reducerPath]: dataCategoriesApi.reducer,
      [dataQualifierApi.reducerPath]: dataQualifierApi.reducer,
      [dataSubjectsApi.reducerPath]: dataSubjectsApi.reducer,
      [dataUseApi.reducerPath]: dataUseApi.reducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(
        datasetApi.middleware,
        organizationApi.middleware,
        scannerApi.middleware,
        systemApi.middleware,
        dataCategoriesApi.middleware,
        dataQualifierApi.middleware,
        dataSubjectsApi.middleware,
        dataUseApi.middleware
      ),
  });
  setupListeners(store.dispatch);
  return store;
};

export type AppStore = ReturnType<typeof makeStore>;
export type AppState = ReturnType<AppStore["getState"]>;
export type AppDispatch = AppStore["dispatch"];

export const wrapper = createWrapper<AppStore>(makeStore);
