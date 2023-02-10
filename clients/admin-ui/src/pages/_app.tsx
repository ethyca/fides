import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/700.css";

import { FidesProvider } from "@fidesui/react";
import type { AppProps } from "next/app";
import React from "react";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";

import ProtectedRoute from "~/features/auth/ProtectedRoute";
import CommonSubscriptions from "~/features/common/CommonSubscriptions";

import store, { persistor } from "../app/store";
import theme from "../theme";
import Login from "./login";

if (process.env.NEXT_PUBLIC_MOCK_API) {
  // eslint-disable-next-line global-require
  require("../mocks");
}

const SafeHydrate: React.FC = ({ children }) => (
  <div suppressHydrationWarning>
    {typeof window === "undefined" ? null : children}
  </div>
);

const MyApp = ({ Component, pageProps }: AppProps) => (
  <SafeHydrate>
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <FidesProvider theme={theme}>
          {Component === Login ? (
            // Only the login page is accessible while logged out. If there is
            // a use case for more unprotected routes, Next has a guide for
            // per-page layouts:
            // https://nextjs.org/docs/basic-features/layouts#per-page-layouts
            <Component {...pageProps} />
          ) : (
            <ProtectedRoute>
              <CommonSubscriptions />
              <Component {...pageProps} />
            </ProtectedRoute>
          )}
        </FidesProvider>
      </PersistGate>
    </Provider>
  </SafeHydrate>
);

export default MyApp;
