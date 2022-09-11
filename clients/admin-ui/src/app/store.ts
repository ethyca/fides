import { configureStore, StateFromReducersMapObject } from "@reduxjs/toolkit";
import { setupListeners } from "@reduxjs/toolkit/query/react";

import { STORED_CREDENTIALS_KEY } from "../constants";
import {
  authApi,
  AuthState,
  credentialStorage,
  reducer as authReducer,
} from "../features/auth";
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
import { dispatch } from "jest-circus/build/state";

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
};

export type RootState = StateFromReducersMapObject<typeof reducer>;

export const makeStore = (preloadedState?: Partial<RootState>) =>
  configureStore({
    reducer,
    middleware: (getDefaultMiddleware) =>
      getDefaultMiddleware().concat(
        credentialStorage.middleware,
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
  const storedAuthStateString = localStorage.getItem(STORED_CREDENTIALS_KEY);
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

type AppStore = ReturnType<typeof makeStore>;
export type AppDispatch = AppStore["dispatch"];

setupListeners(store.dispatch);

export default store;
