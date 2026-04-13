import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectConsentModuleEnabled } from "~/features/config-settings/config-settings.slice";
import { ActionType } from "~/types/api";

import { SubjectRequestActionTypeOptions } from "../constants";

export const useSubjectRequestActionTypeOptions = () => {
  const consentModuleEnabled = useAppSelector(selectConsentModuleEnabled);
  return useMemo(
    () =>
      SubjectRequestActionTypeOptions.filter(
        (option) => consentModuleEnabled || option.value !== ActionType.CONSENT,
      ),
    [consentModuleEnabled],
  );
};
