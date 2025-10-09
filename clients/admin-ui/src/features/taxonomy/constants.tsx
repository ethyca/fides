import { ScopeRegistryEnum } from "~/types/api";

export const TAXONOMY_ROOT_NODE_ID = "root";

// Taxonomy type API keys used in API calls
export enum TaxonomyTypeEnum {
  DATA_CATEGORY = "data_category",
  DATA_USE = "data_use",
  DATA_SUBJECT = "data_subject",
  SYSTEM_GROUP = "system_group",
}

// The core taxonomy types that are built-in to Fides
// Built-in taxonomy types cannot be deleted
export enum CoreTaxonomiesEnum {
  DATA_CATEGORIES = "Data categories",
  DATA_USES = "Data uses",
  DATA_SUBJECTS = "Data subjects",
  SYSTEM_GROUPS = "System groups", // Plus-only, but still protected
}

export const taxonomyTypeToLabel = (taxonomyType: string): string => {
  switch (taxonomyType) {
    case TaxonomyTypeEnum.DATA_CATEGORY:
      return CoreTaxonomiesEnum.DATA_CATEGORIES;
    case TaxonomyTypeEnum.DATA_USE:
      return CoreTaxonomiesEnum.DATA_USES;
    case TaxonomyTypeEnum.DATA_SUBJECT:
      return CoreTaxonomiesEnum.DATA_SUBJECTS;
    case TaxonomyTypeEnum.SYSTEM_GROUP:
      return CoreTaxonomiesEnum.SYSTEM_GROUPS;
    default:
      // Fallback to the original key if no mapping is found
      return taxonomyType;
  }
};

export const taxonomyKeyToScopeRegistryEnum = (taxonomyKey: string) => {
  switch (taxonomyKey) {
    case TaxonomyTypeEnum.DATA_CATEGORY:
      return {
        UPDATE: ScopeRegistryEnum.DATA_CATEGORY_UPDATE,
        CREATE: ScopeRegistryEnum.DATA_CATEGORY_CREATE,
        DELETE: ScopeRegistryEnum.DATA_CATEGORY_DELETE,
        READ: ScopeRegistryEnum.DATA_CATEGORY_READ,
      } as const;
    case TaxonomyTypeEnum.DATA_USE:
      return {
        UPDATE: ScopeRegistryEnum.DATA_USE_UPDATE,
        CREATE: ScopeRegistryEnum.DATA_USE_CREATE,
        DELETE: ScopeRegistryEnum.DATA_USE_DELETE,
        READ: ScopeRegistryEnum.DATA_USE_READ,
      } as const;
    case TaxonomyTypeEnum.DATA_SUBJECT:
      return {
        UPDATE: ScopeRegistryEnum.DATA_SUBJECT_UPDATE,
        CREATE: ScopeRegistryEnum.DATA_SUBJECT_CREATE,
        DELETE: ScopeRegistryEnum.DATA_SUBJECT_DELETE,
        READ: ScopeRegistryEnum.DATA_SUBJECT_READ,
      } as const;
    case TaxonomyTypeEnum.SYSTEM_GROUP:
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
      } as const;
  }
};
