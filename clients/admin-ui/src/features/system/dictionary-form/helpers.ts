import { DictDataUse } from "~/features/plus/types";
import { PrivacyDeclarationResponse } from "~/types/api";

export const transformDictDataUseToDeclaration = (
  dataUse: DictDataUse
): PrivacyDeclarationResponse => {
  // fix "Legitimate Interests" capitalization for API
  const legalBasisForProcessing =
    dataUse.legal_basis_for_processing === "Legitimate Interests"
      ? "Legitimate interests"
      : dataUse.legal_basis_for_processing;

  // some data categories are nested on the backend, flatten them
  // https://github.com/ethyca/fides-services/issues/100
  const dataCategories = dataUse.data_categories.flatMap((dc) => dc.split(","));

  return {
    data_use: dataUse.data_use,
    data_categories: dataCategories,
    features: dataUse.features,
    // @ts-ignore
    legal_basis_for_processing: legalBasisForProcessing,
    retention_period: `${dataUse.retention_period}`,
    cookies: dataUse.cookies.map((c) => ({
      name: c.identifier,
      domain: c.domains,
      path: "/",
    })),
  };
};
