import { configureStore } from "@reduxjs/toolkit";
import { setupListeners } from "@reduxjs/toolkit/query/react";
import { createWrapper } from "next-redux-wrapper";

import { reducer as userReducer } from "../features/user";

const makeStore = () => {
  const store = configureStore({
    reducer: {
      user: userReducer,
    },
    middleware: (getDefaultMiddleware) => getDefaultMiddleware(),
  });
  setupListeners(store.dispatch);
  return store;
};

export type AppStore = ReturnType<typeof makeStore>;
export type AppState = ReturnType<AppStore["getState"]>;

export const wrapper = createWrapper<AppStore>(makeStore);
