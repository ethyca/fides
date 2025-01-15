import { useMemo } from "react";

import { SpecialCategoryLegalBasisEnum } from "~/types/api";

const useSpecialCategoryLegalBasisOptions = () => {
  const specialCategoryLegalBasisOptions = useMemo(
    () =>
      (
        Object.keys(SpecialCategoryLegalBasisEnum) as Array<
          keyof typeof SpecialCategoryLegalBasisEnum
        >
      ).map((key) => ({
        value: SpecialCategoryLegalBasisEnum[key],
        label: SpecialCategoryLegalBasisEnum[key],
      })),
    [],
  );

  return { specialCategoryLegalBasisOptions };
};

export default useSpecialCategoryLegalBasisOptions;
