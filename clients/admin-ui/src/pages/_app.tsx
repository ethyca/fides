import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/700.css";

import { ChakraProvider } from "@chakra-ui/react";
import type { AppProps } from "next/app";
import React from "react";
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import { FlagsProvider } from "react-feature-flags";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";

import ProtectedRoute from "~/features/auth/ProtectedRoute";
import CommonSubscriptions from "~/features/common/CommonSubscriptions";

import store, { persistor } from "../app/store";
import flags from "../flags.json";
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
  <FlagsProvider value={flags}>
    <SafeHydrate>
      <Provider store={store}>
        <PersistGate loading={null} persistor={persistor}>
          <ChakraProvider theme={theme}>
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
          </ChakraProvider>
        </PersistGate>
      </Provider>
    </SafeHydrate>
  </FlagsProvider>
);

export default MyApp;
