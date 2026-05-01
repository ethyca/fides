import { useMemo } from "react";

import { decodePolicyKey } from "~/common/policy-key";
import { useConfig } from "~/features/common/config.slice";
import { PrivacyRequestOption } from "~/types/config";

/**
 * Looks up a PrivacyRequestOption from the config based on an encoded action key
 * from the route params. Used by the form, verification, and success pages.
 */
const useActionFromRoute = (
  actionKey: string | undefined,
): PrivacyRequestOption | undefined => {
  const config = useConfig();
  return useMemo(() => {
    if (!actionKey) {
      return undefined;
    }
    const decoded = decodePolicyKey(actionKey);
    const colonIndex = decoded.indexOf(":");
    const actionIndex =
      colonIndex !== -1 ? parseInt(decoded.slice(0, colonIndex), 10) : NaN;
    const policyKey =
      colonIndex !== -1 ? decoded.slice(colonIndex + 1) : decoded;
    const actions = config.actions ?? [];
    return (
      !Number.isNaN(actionIndex) &&
      actions[actionIndex]?.policy_key === policyKey
        ? actions[actionIndex]
        : actions.find((a) => a.policy_key === policyKey)
    ) as PrivacyRequestOption | undefined;
  }, [actionKey, config.actions]);
};

export default useActionFromRoute;
