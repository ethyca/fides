import { configureStore } from "@reduxjs/toolkit";
import { setupListeners } from "@reduxjs/toolkit/query/react";
import { createWrapper } from "next-redux-wrapper";
import {
  organizationApi,
  reducer as organizationReducer,
} from "~/features/config-wizard/organization.slice";
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
      organization: organizationReducer,
      [datasetApi.reducerPath]: datasetApi.reducer,
      [organizationApi.reducerPath]: organizationApi.reducer,
      [systemApi.reducerPath]: systemApi.reducer,
      [dataCategoriesApi.reducerPath]: dataCategoriesApi.reducer,
    },
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(
        datasetApi.middleware,
        organizationApi.middleware,
        systemApi.middleware,
        dataCategoriesApi.middleware
      ),
  });
  setupListeners(store.dispatch);
  return store;
};

export type AppStore = ReturnType<typeof makeStore>;
export type AppState = ReturnType<AppStore["getState"]>;

export const wrapper = createWrapper<AppStore>(makeStore);
