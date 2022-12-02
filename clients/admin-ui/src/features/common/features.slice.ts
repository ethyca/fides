import { useAppSelector } from "~/app/hooks";
import { selectHealth, useHasPlus } from "~/features/plus/plus.slice";

/**
 * Features are currently stateless and only use the Plus API. However, this a ".slice" file because
 * it is likely the feature toggles will require state and/or the use of other APIs
 */
export interface Features {
  plus: boolean;
  dataFlowScanning: boolean;
}

export const useFeatures = (): Features => {
  const hasPlus = useHasPlus();
  const health = useAppSelector(selectHealth);

  const dataFlowScanning = health ? !!health.system_scanner.enabled : false;

  return {
    plus: hasPlus,
    dataFlowScanning,
  };
};
