import { useMemo } from "react";

import { useGetAllConnectionTypesQuery } from "~/features/connection-type";
import { SaasConnectionTypes } from "~/features/integrations/types/SaasConnectionTypes";
import { ConnectionType } from "~/types/api/models/ConnectionType";

const useIntegrationOption = (
  type?: ConnectionType,
  saasType?: SaasConnectionTypes,
) => {
  const { data: connectionOptions } = useGetAllConnectionTypesQuery({});
  const selectedOption = useMemo(() => {
    if (type === ConnectionType.SAAS) {
      return connectionOptions?.items.find(
        (opt) => opt.identifier === saasType,
      );
    }
    return connectionOptions?.items.find((opt) => opt.identifier === type);
  }, [connectionOptions, type, saasType]);
  return selectedOption;
};

export default useIntegrationOption;
