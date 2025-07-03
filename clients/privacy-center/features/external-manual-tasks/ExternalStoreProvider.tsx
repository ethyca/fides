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
import { loadConfig } from "~/features/common/config.slice";
import { loadSettings } from "~/features/common/settings.slice";
import { PrivacyCenterConfig } from "~/types/api";
import { Config } from "~/types/config";

import externalStore, { externalPersistor } from "./store";

interface ExternalStoreProviderProps {
  children: ReactNode;
  settings: PrivacyCenterClientSettings;
  config?: Config | PrivacyCenterConfig;
}

/**
 * Component to load settings and config into external store
 */
const StoreDataLoader = ({
  children,
  settings,
  config,
}: {
  children: ReactNode;
  settings: PrivacyCenterClientSettings;
  config?: Config | PrivacyCenterConfig;
}): React.ReactElement => {
  useEffect(() => {
    // Load settings into external store
    externalStore.dispatch(loadSettings(settings));

    // Load config into external store if available
    if (config) {
      externalStore.dispatch(loadConfig(config));
    }
  }, [settings, config]);

  return children as React.ReactElement;
};

const ExternalStoreProvider = ({
  children,
  settings,
  config,
}: ExternalStoreProviderProps) => {
  return (
    <Provider store={externalStore}>
      <PersistGate loading={null} persistor={externalPersistor}>
        <StoreDataLoader settings={settings} config={config}>
          {children}
        </StoreDataLoader>
      </PersistGate>
    </Provider>
  );
};

export default ExternalStoreProvider;
