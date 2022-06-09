import { configureStore, StateFromReducersMapObject } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query/react';

import { STORED_CREDENTIALS_KEY } from '../constants';
import {
  authApi,
  AuthState,
  credentialStorage,
  reducer as authReducer,
} from '../features/auth';
import {
  privacyRequestApi,
  reducer as privacyRequestsReducer,
} from '../features/privacy-requests';
import {
  reducer as userManagementReducer,
  userApi,
} from '../features/user-management';

const reducer = {
  [privacyRequestApi.reducerPath]: privacyRequestApi.reducer,
  subjectRequests: privacyRequestsReducer,
  [userApi.reducerPath]: userApi.reducer,
  [authApi.reducerPath]: authApi.reducer,
  userManagement: userManagementReducer,
  auth: authReducer,
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
        authApi.middleware
      ),
    devTools: true,
    preloadedState,
  });

let storedAuthState: AuthState | undefined;
if (typeof window !== 'undefined' && 'localStorage' in window) {
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

setupListeners(store.dispatch);

export default store;
