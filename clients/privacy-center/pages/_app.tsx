import App, { AppContext, AppInitialProps, AppProps } from "next/app";
import Head from "next/head";
import { useMemo } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { Provider } from "react-redux";
import { persistStore } from "redux-persist";
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

import {
  hydratePrivacyCenterEnvironment,
  loadPrivacyCenterEnvironment,
  PrivacyCenterEnvironment,
} from "~/app/server-environment";
import store from "~/app/store";
import Error from "~/components/Error";
import { loadConfig } from "~/features/common/config.slice";
import theme from "~/theme";

interface PrivacyCenterProps {
  serverEnvironment?: PrivacyCenterEnvironment;
}

/**
 * Perform any server-side initialization for the app.
 *
 * We use this to do things like:
 * - read ENV vars for customization
 * - fetch the "config.json" configuration files
 * - etc.
 *
 * DEFER: Custom apps do not support "getServerSideProps" for data fetching, etc.
 * While this "getInitialProps" works, NextJS 13+ supports a new "app/"
 * directory which has a cleaner abstraction for this kind of server-side
 * component logic. We should migrate to this when we're ready!
 * (see https://beta.nextjs.org/docs/upgrade-guide)
 */
export async function getInitialProps(
  context: AppContext
): Promise<PrivacyCenterProps & AppInitialProps> {
  // NOTE: NextJS *requires* we call this and merge the results into the output
  // see https://nextjs.org/docs/advanced-features/custom-app#caveats
  const ctx = await App.getInitialProps(context);
  const isServer = typeof window === "undefined";
  if (!isServer) {
    // Handle the case where this runs on the client - which we don't *really*
    // want to happen, but since getServerSideProps isn't supported for custom
    // Apps in NextJS 12, we have to guard against this possibility...
    return ctx;
  }

  // Load the server-side environment for the session and pass it to the client as props
  const serverEnvironment = await loadPrivacyCenterEnvironment();
  return {
    ...ctx,
    ...{ serverEnvironment },
  };
}

const SafeHydrate: React.FC = ({ children }) => (
  <div suppressHydrationWarning>
    {typeof window === "undefined" ? null : children}
  </div>
);

const PrivacyCenterApp = ({
  Component,
  pageProps,
  serverEnvironment,
}: PrivacyCenterProps & AppProps) => {
  const environment = useMemo(() => {
    console.log("_app.useMemo initializing...");
    const env = hydratePrivacyCenterEnvironment(serverEnvironment);
    store.dispatch(loadConfig(env?.config));
    return env;
  }, [serverEnvironment]);
  console.log("render app");
  return (
    <SafeHydrate>
      <Provider store={store}>
        <PersistGate onBeforeLift={() => console.log("onBeforeLift")} loading={<div>Loading...</div>} persistor={persistStore(store)}>
          <ChakraProvider theme={theme}>
            <ErrorBoundary fallbackRender={Error}>
              <Head>
                <title>Privacy Center</title>
                <meta name="description" content="Privacy Center" />
                <link rel="icon" href="/favicon.ico" />
                {environment?.styles ? <style>{environment.styles}</style> : null}
              </Head>
              <Component {...pageProps} />
            </ErrorBoundary>
          </ChakraProvider>
        </PersistGate>
      </Provider>
    </SafeHydrate>
  );
};

PrivacyCenterApp.getInitialProps = getInitialProps;

export default PrivacyCenterApp;
