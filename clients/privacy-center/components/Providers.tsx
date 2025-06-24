"use client";

import { ErrorBoundary } from "react-error-boundary";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";

import { AntThemeConfig, FidesUIProvider } from "~/../fidesui/src";
import { I18nProvider } from "~/common/i18nContext";
import Error from "~/components/Error";
import theme from "~/theme";

import store, { persistor } from "../app/store";

// Ant Design theme configuration for privacy center
const antTheme: AntThemeConfig = {
  // Basic theme configuration can go here if needed
};

interface ProvidersProps {
  children: React.ReactNode;
}

const Providers = ({ children }: ProvidersProps) => (
  <Provider store={store}>
    <I18nProvider>
      <PersistGate persistor={persistor}>
        <FidesUIProvider
          theme={theme}
          antTheme={antTheme}
          wave={{ disabled: true }}
        >
          <ErrorBoundary fallbackRender={Error}>{children}</ErrorBoundary>
        </FidesUIProvider>
      </PersistGate>
    </I18nProvider>
  </Provider>
);
export default Providers;
