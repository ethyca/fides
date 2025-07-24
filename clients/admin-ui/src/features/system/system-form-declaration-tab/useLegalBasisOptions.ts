import { useMemo } from "react";

import { LegalBasisForProcessingEnum } from "~/types/api";

const useLegalBasisOptions = () => {
  const legalBasisOptions = useMemo(
    () =>
      (
        Object.keys(LegalBasisForProcessingEnum) as Array<
          keyof typeof LegalBasisForProcessingEnum
        >
      ).map((key) => ({
        value: LegalBasisForProcessingEnum[key],
        label: LegalBasisForProcessingEnum[key],
      })),
    [],
  );

  return { legalBasisOptions };
};

export default useLegalBasisOptions;
