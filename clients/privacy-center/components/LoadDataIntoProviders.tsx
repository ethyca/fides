"use client";
import { useEffect, useState } from "react";
import { PrivacyCenterEnvironment } from "~/app/server-environment";
import store from "~/app/store";
import { loadConfig } from "~/features/common/config.slice";
import { loadProperty } from "~/features/common/property.slice";
import { loadSettings } from "~/features/common/settings.slice";
import { loadStyles } from "~/features/common/styles.slice";
import { setLocation } from "~/features/consent/consent.slice";

interface LoadDataIntoProvidersProps {
  children: React.ReactNode;
  serverEnvironment: PrivacyCenterEnvironment;
}

/**
 * Component that loads the server environment data into the Redux store.
 * This is used to load the store with the server data before rendering the application.
 *
 * @param {ReactNode} children - The children elements to be rendered within the layout.
 * @param {PrivacyCenterEnvironment} serverEnvironment - The server environment data to be loaded into the store.
 * @returns {ReactElement} The rendered layout component.
 */

const LoadDataIntoProviders = ({
  children,
  serverEnvironment,
}: LoadDataIntoProvidersProps) => {
  const [hasInitializedStores, setHasInitializedStores] = useState(false);

  useEffect(() => {
    if (serverEnvironment) {
      // Load the server environment into the Redux store
      store.dispatch(loadSettings(serverEnvironment.settings));
      store.dispatch(loadConfig(serverEnvironment.config));
      store.dispatch(loadStyles(serverEnvironment.styles));
      store.dispatch(loadProperty(serverEnvironment.property));
      store.dispatch(setLocation(serverEnvironment.location?.location));
      setHasInitializedStores(true);
    }
  }, [serverEnvironment]);

  return <div>{hasInitializedStores && children}</div>;
};
export default LoadDataIntoProviders;
