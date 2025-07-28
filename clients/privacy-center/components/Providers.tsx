"use client";

import { useEffect } from "react";
import { ErrorBoundary } from "react-error-boundary";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";

import { defaultAntTheme, FidesUIProvider } from "~/../fidesui/src";
import { I18nProvider } from "~/common/i18nContext";
import Error from "~/components/Error";
import theme from "~/theme";

import store, { persistor } from "../app/store";

interface ProvidersProps {
  children: React.ReactNode;
}

// Separate component to initialize fidesDebugger on client side
const FidesDebuggerInit = () => {
  useEffect(() => {
    if (typeof (globalThis as any).fidesDebugger === 'undefined') {
      // Use the same debug logic as server-side: FIDES_PRIVACY_CENTER__DEBUG or fall back to development mode
      const isDebugMode = process.env.FIDES_PRIVACY_CENTER__DEBUG === "true" ||
                         (process.env.FIDES_PRIVACY_CENTER__DEBUG === undefined && process.env.NODE_ENV === 'development');
      const debugMarker = "=>";
      (globalThis as any).fidesDebugger = isDebugMode
        ? (...args: unknown[]) => console.log(`\x1b[33m${debugMarker}\x1b[0m`, ...args)
        : () => {};
      (globalThis as any).fidesError = isDebugMode
        ? (...args: unknown[]) => console.log(`\x1b[31m${debugMarker}\x1b[0m`, ...args)
        : () => {};
    }
  }, []);

  return null;
};

const Providers = ({ children }: ProvidersProps) => (
  <Provider store={store}>
    <FidesDebuggerInit />
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
