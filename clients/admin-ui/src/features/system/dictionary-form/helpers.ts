import { PrivacyDeclarationResponse } from "~/types/api";
import { DataUseDeclaration } from "~/types/dictionary-api";

export const transformDictDataUseToDeclaration = (
  dataUse: DataUseDeclaration,
): Omit<PrivacyDeclarationResponse, "id"> => {
  // some data categories are nested on the backend, flatten them
  // https://github.com/ethyca/fides-services/issues/100
  const dataCategories = dataUse.data_categories.flatMap((dc) => dc.split(","));

  return {
    data_use: dataUse.data_use,
    data_categories: dataCategories,
    features: dataUse.features,
    legal_basis_for_processing: dataUse.legal_basis_for_processing,
    flexible_legal_basis_for_processing:
      dataUse.flexible_legal_basis_for_processing,
    retention_period: dataUse.retention_period ? dataUse.retention_period : "",
    cookies: dataUse.cookies?.map((c) => ({
      name: c.name,
      domain: c.domain,
      path: c.path,
    })),
  };
};
