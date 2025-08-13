import { useEffect, useState } from "react";

import { DEFAULT_SYSTEM_GROUPS } from "~/mocks/TEMP-system-groups/endpoints/systems";
import { SystemGroupCreate } from "~/mocks/TEMP-system-groups/types";

export const useMockGetSystemGroupsQuery = () => {
  const [isLoading, setIsLoading] = useState(false);
  useEffect(() => {
    setIsLoading(true);
    setTimeout(() => {
      setIsLoading(false);
    }, 200);
  }, []);

  if (isLoading) {
    return {
      data: undefined,
      isLoading,
    };
  }

  return {
    data: DEFAULT_SYSTEM_GROUPS,
    isLoading,
  };
};

export const useMockCreateSystemGroupMutation = () => {
  const create = async (systemGroup: SystemGroupCreate) => {
    // eslint-disable-next-line no-promise-executor-return
    await new Promise((resolve) => setTimeout(resolve, 200));
    return {
      data: systemGroup,
    };
  };
  return [create];
};
