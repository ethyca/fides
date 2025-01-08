import "@fontsource/inter/400.css";
import "@fontsource/inter/500.css";
import "@fontsource/inter/600.css";
import "@fontsource/inter/700.css";
import "../theme/global.scss";

import { FidesUIProvider } from "fidesui";
import App, { AppContext, AppInitialProps, AppProps } from "next/app";
import { ReactNode, useMemo } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";

import {
  loadPrivacyCenterEnvironment,
  PrivacyCenterEnvironment,
} from "~/app/server-environment";
import store, { persistor } from "~/app/store";
import { I18nProvider } from "~/common/i18nContext";
import Error from "~/components/Error";
import Layout from "~/components/Layout";
import { loadConfig } from "~/features/common/config.slice";
import { loadProperty } from "~/features/common/property.slice";
import { loadSettings } from "~/features/common/settings.slice";
import { loadStyles } from "~/features/common/styles.slice";
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
  context: AppContext,
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
  const customPropertyPath =
    context.router.query.customPropertyPath?.toString();
  const serverEnvironment = await loadPrivacyCenterEnvironment({
    customPropertyPath,
  });

  return {
    ...ctx,
    ...{ serverEnvironment },
  };
}

const SafeHydrate = ({ children }: { children: ReactNode }) => (
  <div suppressHydrationWarning>
    {typeof window === "undefined" ? null : children}
  </div>
);

const PrivacyCenterApp = ({
  Component,
  pageProps,
  serverEnvironment,
}: PrivacyCenterProps & AppProps) => {
  useMemo(() => {
    if (serverEnvironment) {
      // Load the server environment into the Redux store
      store.dispatch(loadSettings(serverEnvironment.settings));
      store.dispatch(loadConfig(serverEnvironment.config));
      store.dispatch(loadStyles(serverEnvironment.styles));
      store.dispatch(loadProperty(serverEnvironment.property));
    }
  }, [serverEnvironment]);
  return (
    <SafeHydrate>
      <Provider store={store}>
        <I18nProvider>
          <PersistGate persistor={persistor}>
            <FidesUIProvider theme={theme}>
              <ErrorBoundary fallbackRender={Error}>
                <Layout>
                  <Component {...pageProps} />
                </Layout>
              </ErrorBoundary>
            </FidesUIProvider>
          </PersistGate>
        </I18nProvider>
      </Provider>
    </SafeHydrate>
  );
};

PrivacyCenterApp.getInitialProps = getInitialProps;

export default PrivacyCenterApp;
