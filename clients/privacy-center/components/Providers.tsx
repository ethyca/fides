"use client";

import { ErrorBoundary } from "react-error-boundary";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";

import { defaultAntTheme, FidesUIProvider } from "~/../fidesui/src";
import { I18nProvider } from "~/common/i18nContext";
import Error from "~/components/Error";
import VersionLogger from "~/components/VersionLogger";
import theme from "~/theme";

import store, { persistor } from "../app/store";

interface ProvidersProps {
  children: React.ReactNode;
  version: string;
}

const Providers = ({ children, version }: ProvidersProps) => (
  <Provider store={store}>
    <VersionLogger version={version} />
    <I18nProvider>
      <PersistGate persistor={persistor}>
        <FidesUIProvider
          theme={theme}
          antTheme={defaultAntTheme}
          wave={{ disabled: true }}
        >
          <ErrorBoundary fallbackRender={Error}>{children}</ErrorBoundary>
        </FidesUIProvider>
      </PersistGate>
    </I18nProvider>
  </Provider>
);
export default Providers;
