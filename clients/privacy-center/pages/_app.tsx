import type { AppProps } from "next/app";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";
/*
 * This import needed to be updated to '@chakra-ui/react' from "@fidesui/react".
 * Under the hood fidesui is importing from "@chakra-ui/provider" instead "chakra-ui/react".
 * This causes issues with toasts because it doesn't set up everything required for them.
 * Solution found here https://github.com/chakra-ui/chakra-ui/issues/5839#issuecomment-1266493711
 * */
import { ChakraProvider } from "@chakra-ui/react";

import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";

import store, { persistor } from "~/app/store";
import "~/config/config.css";
import theme from "~/theme";
import { useFidesUserDeviceIdCookie } from "~/common/hooks/useCookie";

const SafeHydrate: React.FC = ({ children }) => (
  <div suppressHydrationWarning>
    {typeof window === "undefined" ? null : children}
  </div>
);

const MyApp = ({ Component, pageProps }: AppProps) => {

  useFidesUserDeviceIdCookie();

  return <SafeHydrate>
    <Provider store={store}>
      <PersistGate loading={null} persistor={persistor}>
        <ChakraProvider theme={theme}>
          <Component {...pageProps} />
        </ChakraProvider>
      </PersistGate>
    </Provider>
  </SafeHydrate>
};

export default MyApp;
