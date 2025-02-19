"use server";

import { cache } from "react";

import { lookupGeolocationServerSide } from "~/common/geolocation-server";

import {
  getClientSettings,
  getFidesApiUrl,
  loadConfigFromFile,
  loadStylesFromFile,
  PrivacyCenterEnvironment,
} from "../server-environment";
import debugLogServer from "./debugLogServer";
import fetchPropetyFromApi from "./fetchPropetyFromApi";
import loadEnvironmentVariables from "./loadEnvironmentVariables";

const getPrivacyCenterEnvironment = async ({
  propertyPath,
}: {
  propertyPath?: string;
} = {}): Promise<PrivacyCenterEnvironment> => {
  // DEFER: Log a version number here (see https://github.com/ethyca/fides/issues/3171)
  debugLogServer("Load Privacy Center environment for session...");

  const userLocation = await lookupGeolocationServerSide();
  const envVariables = loadEnvironmentVariables();
  const privacyCenterPath =
    propertyPath || envVariables.ROOT_PROPERTY_PATH || "/";

  // Fetch property from API
  // Only fetch if USE_API_CONFIG is true or propertyPath is provided
  // (property paths are only supported in the api)
  const useApiConfig = Boolean(
    envVariables.USE_API_CONFIG || privacyCenterPath !== "/",
  );
  let property = null;
  if (useApiConfig) {
    property = await fetchPropetyFromApi({
      path: privacyCenterPath,
      fidesApiUrl: getFidesApiUrl(),
      location: userLocation?.location,
    });
  }

  // Load config from property or fallback to static file config
  const config =
    property?.privacy_center_config ||
    (await loadConfigFromFile(envVariables.CONFIG_JSON_URL));

  // Load stylesheets from property or fallback to static file styles
  const styles =
    property?.stylesheet ||
    (await loadStylesFromFile(envVariables.CONFIG_CSS_URL));

  // Get client settings from env variables
  const settings = getClientSettings();

  return {
    settings,
    config,
    styles,
    property,
    location: userLocation || undefined,
  };
};

// Cache the environment to avoid re calculating it when getPrivacyCenterEnvironmentCached
// is called multiple times. The cache only applies to the current request.
// ref: https://react.dev/reference/react/cache
const getPrivacyCenterEnvironmentCached = cache(getPrivacyCenterEnvironment);

export default getPrivacyCenterEnvironmentCached;
