import { ScopeRegistryEnum } from "~/types/api";

export const TAXONOMY_ROOT_NODE_ID = "root";

// The core taxonomy types that are built-in to Fides
// Built-in taxonomy types cannot be deleted
export enum CoreTaxonomiesEnum {
  DATA_CATEGORIES = "Data categories",
  DATA_USES = "Data uses",
  DATA_SUBJECTS = "Data subjects",
}

export const taxonomyTypeToScopeRegistryEnum = (
  taxonomyType: CoreTaxonomiesEnum,
) => {
  switch (taxonomyType) {
    case CoreTaxonomiesEnum.DATA_CATEGORIES:
      return {
        UPDATE: ScopeRegistryEnum.DATA_CATEGORY_UPDATE,
        CREATE: ScopeRegistryEnum.DATA_CATEGORY_CREATE,
        DELETE: ScopeRegistryEnum.DATA_CATEGORY_DELETE,
        READ: ScopeRegistryEnum.DATA_CATEGORY_READ,
      };
    case CoreTaxonomiesEnum.DATA_USES:
      return {
        UPDATE: ScopeRegistryEnum.DATA_USE_UPDATE,
        CREATE: ScopeRegistryEnum.DATA_USE_CREATE,
        DELETE: ScopeRegistryEnum.DATA_USE_DELETE,
        READ: ScopeRegistryEnum.DATA_USE_READ,
      };
    case CoreTaxonomiesEnum.DATA_SUBJECTS:
      return {
        UPDATE: ScopeRegistryEnum.DATA_SUBJECT_UPDATE,
        CREATE: ScopeRegistryEnum.DATA_SUBJECT_CREATE,
        DELETE: ScopeRegistryEnum.DATA_SUBJECT_DELETE,
        READ: ScopeRegistryEnum.DATA_SUBJECT_READ,
      };
  }
};
