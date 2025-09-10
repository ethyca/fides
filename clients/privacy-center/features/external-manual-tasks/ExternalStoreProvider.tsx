/**
 * External Store Provider
 *
 * COPIED & ADAPTED FROM: clients/admin-ui/src/app/providers/app-store-provider.tsx
 *
 * Provides Redux store and persistence for external manual tasks
 */

"use client";

import React, { ReactNode, useEffect, useState } from "react";
import { Provider } from "react-redux";
import { PersistGate } from "redux-persist/integration/react";

import { PrivacyCenterClientSettings } from "~/app/server-environment";
import { loadConfig } from "~/features/common/config.slice";
import { loadSettings } from "~/features/common/settings.slice";
import { fides__api__schemas__privacy_center_config__PrivacyCenterConfig as PrivacyCenterConfig } from "~/types/api";
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
}): React.ReactElement | null => {
  const [hasInitializedStores, setHasInitializedStores] = useState(false);

  useEffect(() => {
    // Load settings into external store
    externalStore.dispatch(loadSettings(settings));

    // Load config into external store if available
    if (config) {
      externalStore.dispatch(loadConfig(config));
    }

    // Mark stores as initialized so children can render
    setHasInitializedStores(true);
  }, [settings, config]);

  if (!hasInitializedStores) {
    return null;
  }

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
