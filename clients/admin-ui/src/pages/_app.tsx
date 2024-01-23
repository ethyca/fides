import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/700.css";

import { FidesProvider, Flex } from "@fidesui/react";
import type { AppProps } from "next/app";
import React from "react";
import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";

import ProtectedRoute from "~/features/auth/ProtectedRoute";
import CommonSubscriptions from "~/features/common/CommonSubscriptions";
import MainSideNav from "~/features/common/nav/v2/MainSideNav";

import store, { persistor } from "../app/store";
import theme from "../theme";
import Login from "./login";

if (process.env.NEXT_PUBLIC_MOCK_API) {
  // eslint-disable-next-line global-require
  require("../mocks");
}

const SafeHydrate: React.FC = ({ children }) => (
  <div suppressHydrationWarning style={{ height: "100%", display: "flex" }}>
    {typeof window === "undefined" ? null : children}
  </div>
);

const MyApp = ({ Component, pageProps }: AppProps) => (
  <SafeHydrate>
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <FidesProvider theme={theme}>
          <DndProvider backend={HTML5Backend}>
            {Component === Login ? (
              // Only the login page is accessible while logged out. If there is
              // a use case for more unprotected routes, Next has a guide for
              // per-page layouts:
              // https://nextjs.org/docs/basic-features/layouts#per-page-layouts
              <Component {...pageProps} />
            ) : (
              <ProtectedRoute>
                <CommonSubscriptions />
                <Flex width="100%" height="100%" flex={1}>
                  <MainSideNav />
                  <Flex direction="column" width="100%">
                    <Component {...pageProps} />
                  </Flex>
                </Flex>
              </ProtectedRoute>
            )}
          </DndProvider>
        </FidesProvider>
      </PersistGate>
    </Provider>
  </SafeHydrate>
);

export default MyApp;
