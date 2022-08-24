import { configureStore } from "@reduxjs/toolkit";
import { setupListeners } from "@reduxjs/toolkit/query/react";
import { createWrapper } from "next-redux-wrapper";

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
import { systemApi } from "~/features/system";
import { reducer as taxonomyReducer, taxonomyApi } from "~/features/taxonomy";
import { reducer as userReducer } from "~/features/user";

const makeStore = () => {
  const store = configureStore({
    reducer: {
      configWizard: configWizardReducer,
      user: userReducer,
      dataset: datasetReducer,
      taxonomy: taxonomyReducer,
      dataQualifier: dataQualifierReducer,
      dataSubjects: dataSubjectsReducer,
      dataUse: dataUseReducer,
      organization: organizationReducer,
      [datasetApi.reducerPath]: datasetApi.reducer,
      [organizationApi.reducerPath]: organizationApi.reducer,
      [scannerApi.reducerPath]: scannerApi.reducer,
      [systemApi.reducerPath]: systemApi.reducer,
      [taxonomyApi.reducerPath]: taxonomyApi.reducer,
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
        taxonomyApi.middleware,
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
