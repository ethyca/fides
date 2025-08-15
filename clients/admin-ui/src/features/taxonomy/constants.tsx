import { ScopeRegistryEnum } from "~/types/api";

export const TAXONOMY_ROOT_NODE_ID = "root";

// The core taxonomy types that are built-in to Fides
// Built-in taxonomy types cannot be deleted
export enum CoreTaxonomiesEnum {
  DATA_CATEGORIES = "Data categories",
  DATA_USES = "Data uses",
  DATA_SUBJECTS = "Data subjects",
  SYSTEM_GROUPS = "System groups", // Plus-only, but still protected
}

export const taxonomyKeyToScopeRegistryEnum = (taxonomyKey: string) => {
  switch (taxonomyKey) {
    case "data_category":
      return {
        UPDATE: ScopeRegistryEnum.DATA_CATEGORY_UPDATE,
        CREATE: ScopeRegistryEnum.DATA_CATEGORY_CREATE,
        DELETE: ScopeRegistryEnum.DATA_CATEGORY_DELETE,
        READ: ScopeRegistryEnum.DATA_CATEGORY_READ,
      } as const;
    case "data_use":
      return {
        UPDATE: ScopeRegistryEnum.DATA_USE_UPDATE,
        CREATE: ScopeRegistryEnum.DATA_USE_CREATE,
        DELETE: ScopeRegistryEnum.DATA_USE_DELETE,
        READ: ScopeRegistryEnum.DATA_USE_READ,
      } as const;
    case "data_subject":
      return {
        UPDATE: ScopeRegistryEnum.DATA_SUBJECT_UPDATE,
        CREATE: ScopeRegistryEnum.DATA_SUBJECT_CREATE,
        DELETE: ScopeRegistryEnum.DATA_SUBJECT_DELETE,
        READ: ScopeRegistryEnum.DATA_SUBJECT_READ,
      } as const;
    case "system_group":
      return {
        UPDATE: ScopeRegistryEnum.SYSTEM_GROUP_UPDATE,
        CREATE: ScopeRegistryEnum.SYSTEM_GROUP_CREATE,
        DELETE: ScopeRegistryEnum.SYSTEM_GROUP_DELETE,
        READ: ScopeRegistryEnum.SYSTEM_GROUP_READ,
      } as const;
    case "system_groups":
      return {
        UPDATE: ScopeRegistryEnum.SYSTEM_GROUP_UPDATE,
        CREATE: ScopeRegistryEnum.SYSTEM_GROUP_CREATE,
        DELETE: ScopeRegistryEnum.SYSTEM_GROUP_DELETE,
        READ: ScopeRegistryEnum.SYSTEM_GROUP_READ,
      } as const;
    default:
      return {
        UPDATE: ScopeRegistryEnum.TAXONOMY_UPDATE,
        CREATE: ScopeRegistryEnum.TAXONOMY_CREATE,
        DELETE: ScopeRegistryEnum.TAXONOMY_DELETE,
        READ: ScopeRegistryEnum.TAXONOMY_UPDATE,
      } as const;
  }
};
