import App, { AppContext, AppInitialProps, AppProps } from "next/app";
import { useMemo } from "react";
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
import { AppStore, makeStore } from "~/app/store";
import theme from "~/theme";
import Head from "next/head";

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

/**
 *
 * Hydrate the environment and the Redux store using the server-side environment
 *
 * DEFER: ensure this can only happen *once* per session, to avoid unexpected
 * issues where the environment changes unexpected - probably due to a logic
 * error in our app - and we change out the state. The NextJS withRedux() wrapper
 * might handle this? This will allow us to remove all the `console.warn`s...
 * (see https://github.com/ethyca/fides/issues/3212)
 *
 * NOTE: the official NextJS withRedux() wrapper might handle this?
 */
const hydrateEnvironmentAndStore = (
  serverEnvironment?: PrivacyCenterEnvironment
): { environment: PrivacyCenterEnvironment; store: AppStore } => {
  if (!serverEnvironment) {
    console.warn(
      "hydrateEnvironmentAndStore() called without a valid server environment!"
    );
  }
  // Initialize the environment
  const environment = hydratePrivacyCenterEnvironment(serverEnvironment);

  // Initialize the store
  let store;
  if (!environment || !environment.config) {
    console.warn(
      "makeStore being called with empty env or config",
      environment
    );
    store = makeStore();
  } else {
    store = makeStore({ config: { config: environment.config } });
  }

  // The store is exposed on the window object when running in the Cypress test
  // environment. This enables the custom `cy.dispatch` command.
  if (typeof window !== "undefined" && window.Cypress) {
    window.store = store;
  }

  return { environment, store };
};

const PrivacyCenterApp = ({
  Component,
  pageProps,
  serverEnvironment,
}: PrivacyCenterProps & AppProps) => {
  // DEFER: ensure this initializes only once -- and safely! (see https://github.com/ethyca/fides/issues/3212)
  const { environment, store } = useMemo(
    () => hydrateEnvironmentAndStore(serverEnvironment),
    [serverEnvironment]
  );
  return (
    <SafeHydrate>
      <Provider store={store}>
        <PersistGate loading={null} persistor={persistStore(store)}>
          <ChakraProvider theme={theme}>
            <Head>
              <title>Privacy Center</title>
              <meta name="description" content="Privacy Center" />
              <link rel="icon" href="/favicon.ico" />
              {environment.styles ? <style>{environment.styles}</style> : null}
            </Head>
            <Component {...pageProps} />
          </ChakraProvider>
        </PersistGate>
      </Provider>
    </SafeHydrate>
  );
};

PrivacyCenterApp.getInitialProps = getInitialProps;

export default PrivacyCenterApp;
