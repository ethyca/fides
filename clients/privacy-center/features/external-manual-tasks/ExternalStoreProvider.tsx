/**
 * External Store Provider
 *
 * COPIED & ADAPTED FROM: clients/admin-ui/src/app/providers/app-store-provider.tsx
 *
 * Provides Redux store and persistence for external manual tasks
 */

"use client";

import React, { ReactNode, useEffect } from "react";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";

import { PrivacyCenterClientSettings } from "~/app/server-environment";
import { loadSettings } from "~/features/common/settings.slice";

import externalStore, { externalPersistor } from "./store";

interface ExternalStoreProviderProps {
  children: ReactNode;
  settings: PrivacyCenterClientSettings;
}

/**
 * Component to load settings into external store
 */
const SettingsLoader = ({
  children,
  settings,
}: {
  children: ReactNode;
  settings: PrivacyCenterClientSettings;
}) => {
  useEffect(() => {
    // Load settings into external store
    externalStore.dispatch(loadSettings(settings));
  }, [settings]);

  return children;
};

const ExternalStoreProvider = ({
  children,
  settings,
}: ExternalStoreProviderProps) => {
  return (
    <Provider store={externalStore}>
      <PersistGate loading={null} persistor={externalPersistor}>
        <SettingsLoader settings={settings}>{children}</SettingsLoader>
      </PersistGate>
    </Provider>
  );
};

export default ExternalStoreProvider;
