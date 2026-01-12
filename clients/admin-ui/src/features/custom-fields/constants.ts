import { LegacyResourceTypes } from "~/features/common/custom-fields/types";
import { TaxonomyTypeEnum } from "~/features/taxonomy/constants";

export const RESOURCE_TYPE_MAP = new Map([
  [LegacyResourceTypes.SYSTEM, "system:information"],
  [LegacyResourceTypes.DATA_USE, "taxonomy:data use"],
  [LegacyResourceTypes.DATA_CATEGORY, "taxonomy:data category"],
  [LegacyResourceTypes.DATA_SUBJECT, "taxonomy:data subject"],
  [LegacyResourceTypes.PRIVACY_DECLARATION, "system:data use"],
]);

export const VALUE_TYPE_RESOURCE_TYPE_MAP: Record<string, string> = {
  [TaxonomyTypeEnum.DATA_CATEGORY]: "taxonomy:data category",
  [TaxonomyTypeEnum.DATA_USE]: "taxonomy:data use",
  [TaxonomyTypeEnum.DATA_SUBJECT]: "taxonomy:data subject",
  [TaxonomyTypeEnum.SYSTEM_GROUP]: "taxonomy:system group",
};

export const FIDES_KEY_RESOURCE_TYPE_MAP: Record<string, string> = {
  [TaxonomyTypeEnum.DATA_CATEGORY]: LegacyResourceTypes.DATA_CATEGORY,
  [TaxonomyTypeEnum.DATA_USE]: LegacyResourceTypes.DATA_USE,
  [TaxonomyTypeEnum.DATA_SUBJECT]: LegacyResourceTypes.DATA_SUBJECT,
  [TaxonomyTypeEnum.SYSTEM_GROUP]: "system group",
};

export enum FieldTypes {
  SINGLE_SELECT = "singleSelect",
  MULTIPLE_SELECT = "multipleSelect",
  OPEN_TEXT = "openText",
}

export const FIELD_TYPE_OPTIONS = [
  { label: "Single select", value: FieldTypes.SINGLE_SELECT },
  { label: "Multiple select", value: FieldTypes.MULTIPLE_SELECT },
  { label: "Open text", value: FieldTypes.OPEN_TEXT },
];

export const FIELD_TYPE_LABEL_MAP: Record<FieldTypes, string> = {
  [FieldTypes.SINGLE_SELECT]: "Single-value select",
  [FieldTypes.MULTIPLE_SELECT]: "Multi-value select",
  [FieldTypes.OPEN_TEXT]: "Open text",
};
