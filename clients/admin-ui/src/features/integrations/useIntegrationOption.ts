import { useMemo } from "react";

import { useGetAllConnectionTypesQuery } from "~/features/connection-type";
import { ConnectionType } from "~/types/api";

const useIntegrationOption = (type?: ConnectionType) => {
  const { data: connectionOptions } = useGetAllConnectionTypesQuery({});
  const selectedOption = useMemo(
    () => connectionOptions?.items.find((opt) => opt.identifier === type),
    [connectionOptions, type],
  );
  return selectedOption;
};

export default useIntegrationOption;
