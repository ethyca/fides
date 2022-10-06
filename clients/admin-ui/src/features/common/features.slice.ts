import { useHasPlus } from "./plus.slice";

/**
 * Features are currently stateless and only use the Plus API. However, this a ".slice" file because
 * it is likely the feature toggles will require state and/or the use of other APIs
 */
export interface Features {
  plus: boolean;
}

export const useFeatures = (): Features => {
  const hasPlus = useHasPlus();

  return {
    plus: hasPlus,
  };
};
