import { useMemo } from "react";

import { useGetAllConnectionTypesQuery } from "~/features/connection-type";
import {
  connectionLogoFromConfiguration,
  connectionLogoFromKey,
  connectionLogoFromSystemType,
  type ConnectionLogoSource,
} from "~/features/datastore-connections/ConnectionTypeLogo";
import { ConnectionConfigurationResponse, ConnectionType } from "~/types/api";

/**
 * Custom hook to get the correct logo data for ConnectionTypeLogo component.
 *
 * For SAAS integrations, it finds the corresponding ConnectionSystemTypeMap
 * which contains the encoded_icon property needed for proper logo display.
 * For non-SAAS integrations, it returns the original integration object.
 *
 * @param integration - The connection configuration to get logo data for
 * @returns The appropriate data object for ConnectionTypeLogo component
 */
export const useConnectionLogo = (
  integration?: ConnectionConfigurationResponse,
): ConnectionLogoSource => {
  const { data: connectionTypesData } = useGetAllConnectionTypesQuery({});
  const connectionTypes = useMemo(
    () => connectionTypesData?.items || [],
    [connectionTypesData],
  );

  return useMemo(() => {
    if (!integration) {
      return connectionLogoFromKey("");
    }

    if (
      integration.connection_type === ConnectionType.SAAS &&
      integration.saas_config?.type
    ) {
      const connectionTypeMap = connectionTypes.find(
        (ct) => ct.identifier === integration.saas_config?.type,
      );
      if (connectionTypeMap) {
        return connectionLogoFromSystemType(connectionTypeMap);
      }
    }

    return connectionLogoFromConfiguration(integration);
  }, [integration, connectionTypes]);
};
