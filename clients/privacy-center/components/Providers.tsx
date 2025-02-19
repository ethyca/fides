"use client";

import { useMemo } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";

import { FidesUIProvider } from "~/../fidesui/src";
import { I18nProvider } from "~/common/i18nContext";
import Error from "~/components/Error";
import { loadConfig } from "~/features/common/config.slice";
import { loadProperty } from "~/features/common/property.slice";
import { loadSettings } from "~/features/common/settings.slice";
import { loadStyles } from "~/features/common/styles.slice";
import { setLocation } from "~/features/consent/consent.slice";
import theme from "~/theme";

import { PrivacyCenterEnvironment } from "../app/server-environment";
import store, { persistor } from "../app/store";

interface ProvidersProps {
  serverEnvironment: PrivacyCenterEnvironment;
  children: React.ReactNode;
}

const Providers = ({ serverEnvironment, children }: ProvidersProps) => {
  useMemo(() => {
    if (serverEnvironment) {
      // Load the server environment into the Redux store
      store.dispatch(loadSettings(serverEnvironment.settings));
      store.dispatch(loadConfig(serverEnvironment.config));
      store.dispatch(loadStyles(serverEnvironment.styles));
      store.dispatch(loadProperty(serverEnvironment.property));

      store.dispatch(setLocation(serverEnvironment.location?.location));
    }
  }, [serverEnvironment]);

  return (
    <Provider store={store}>
      <I18nProvider>
        <PersistGate persistor={persistor}>
          <FidesUIProvider theme={theme}>
            <ErrorBoundary fallbackRender={Error}>{children}</ErrorBoundary>
          </FidesUIProvider>
        </PersistGate>
      </I18nProvider>
    </Provider>
  );
};
export default Providers;
