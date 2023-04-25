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
import { makeStore } from "~/app/store";
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
export async function getInitialProps(context: AppContext): Promise<PrivacyCenterProps & AppInitialProps> {
  // NOTE: NextJS *requires* we call this and merge the results into the output
  // see https://nextjs.org/docs/advanced-features/custom-app#caveats
  const ctx = await App.getInitialProps(context);
  const isServer = (typeof window === "undefined");
  if (!isServer) {
    // Handle the case where this runs on the client - which we don't *really*
    // want to happen, but since getServerSideProps isn't supported for custom
    // Apps in NextJS 12, we have to guard against this possibility...
    // NOTE: this *should* be impossible...
    // eslint-disable-next-line no-console
    console.warn("Unexpected App.getInitialProps() call from client-side code!");
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

const PrivacyCenterApp = ({ Component, pageProps, serverEnvironment }: PrivacyCenterProps & AppProps) => {
  // Hydrate the environment and the Redux store using the server-side environment
  // TODO: is this the best practice for this kind of "initialize once per
  // session" logic, or is there a better pattern that I'm missing? useEffect?
  // Look into how the nextjs withRedux wrapper works.
  const environment = useMemo(() => hydratePrivacyCenterEnvironment(serverEnvironment), [serverEnvironment]);
  const store = useMemo(() => makeStore({ config: environment.config }), [environment]);

  // The store is exposed on the window object when running in the Cypress test
  // environment. This enables the custom `cy.dispatch` command.
  if (typeof window !== "undefined" && window.Cypress) {
    window.store = store;
  }
  return (
    <SafeHydrate>
      <Provider store={store}>
        <PersistGate loading={null} persistor={persistStore(store)}>
          <ChakraProvider theme={theme}>
            <Head>
              <title>Privacy Center</title>
              <meta name="description" content="Privacy Center" />
              <link rel="icon" href="/favicon.ico" />
              { environment.styles ?  <style>{environment.styles}</style> : null }
            </Head>
            <Component {...pageProps} />
          </ChakraProvider>
        </PersistGate>
      </Provider>
    </SafeHydrate>
  );
}

PrivacyCenterApp.getInitialProps = getInitialProps;

export default PrivacyCenterApp;
