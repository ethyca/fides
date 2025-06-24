"use client";

// Import React 19 compatibility for Ant Design - must be first
import "@ant-design/v5-patch-for-react-19";

import { ErrorBoundary } from "react-error-boundary";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";

import { FidesUIProvider } from "~/../fidesui/src";
import { I18nProvider } from "~/common/i18nContext";
import Error from "~/components/Error";
import theme from "~/theme";

import store, { persistor } from "../app/store";

interface ProvidersProps {
  children: React.ReactNode;
}

const Providers = ({ children }: ProvidersProps) => (
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
export default Providers;
