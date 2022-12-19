import { useAppSelector } from "~/app/hooks";
import { selectInitialConnections } from "~/features/datastore-connections";
import { selectHealth } from "~/features/plus/plus.slice";
import { selectAllSystems } from "~/features/system";

/**
 * Features are currently stateless and only use the Plus API. However, this a ".slice" file because
 * it is likely the feature toggles will require state and/or the use of other APIs
 */
export interface Features {
  plus: boolean;
  dataFlowScanning: boolean;
  systemsCount: number;
  connectionsCount: number;
  navV2: boolean;
}

export const useFeatures = (): Features => {
  const health = useAppSelector(selectHealth);
  const allSystems = useAppSelector(selectAllSystems);
  const initialConnections = useAppSelector(selectInitialConnections);

  const plus = health !== undefined;
  const dataFlowScanning = health ? !!health.system_scanner.enabled : false;

  const systemsCount = allSystems?.length ?? 0;

  const connectionsCount = initialConnections?.total ?? 0;

  // TODO(#1909): Remove condition when we're ready to release Nav 2.0
  const navV2 = process.env.NODE_ENV === "development";

  return {
    plus,
    dataFlowScanning,
    systemsCount,
    connectionsCount,
    navV2,
  };
};
