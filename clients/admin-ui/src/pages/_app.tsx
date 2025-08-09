import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "../theme/tailwind.css";
import "fidesui/src/ant-theme/global.scss";

import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import {
  Center,
  defaultAntTheme,
  FidesUIProvider,
  Flex,
  Spinner,
} from "fidesui";
import type { AppProps } from "next/app";
import { usePathname } from "next/navigation";
import React, { ReactNode } from "react";
import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";

import ProtectedRoute from "~/features/auth/ProtectedRoute";
import CommonSubscriptions from "~/features/common/CommonSubscriptions";
import MainSideNav from "~/features/common/nav/MainSideNav";

import store, { persistor } from "../app/store";
import theme from "../theme";

dayjs.extend(utc);

if (process.env.NEXT_PUBLIC_MOCK_API) {
  // eslint-disable-next-line global-require
  require("../mocks");
}

const SafeHydrate = ({ children }: { children: ReactNode }) => (
  <div suppressHydrationWarning style={{ height: "100%", display: "flex" }}>
    {typeof window === "undefined" ? null : children}
  </div>
);

const MyApp = ({ Component, pageProps }: AppProps) => {
  const path = usePathname();

  if (path) {
    return (
      <SafeHydrate>
        <Provider store={store}>
          <PersistGate loading={null} persistor={persistor}>
            <FidesUIProvider theme={theme} antTheme={defaultAntTheme}>
              <DndProvider backend={HTML5Backend}>
                {path.startsWith("/login") ? (
                  // Only the login routes are accessible while logged out.
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
            </FidesUIProvider>
          </PersistGate>
        </Provider>
      </SafeHydrate>
    );
  }

  return (
    <Center h="100%" w="100%">
      <Spinner color="primary" size="xl" />
    </Center>
  );
};

export default MyApp;
