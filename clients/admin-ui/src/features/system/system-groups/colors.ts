import { CUSTOM_TAG_COLOR } from "fidesui";

import { CustomTaxonomyColor } from "~/types/api";

export const COLOR_VALUE_MAP: Record<CustomTaxonomyColor, CUSTOM_TAG_COLOR> = {
  [CustomTaxonomyColor.TAXONOMY_WHITE]: CUSTOM_TAG_COLOR.DEFAULT,
  [CustomTaxonomyColor.TAXONOMY_RED]: CUSTOM_TAG_COLOR.ERROR,
  [CustomTaxonomyColor.TAXONOMY_ORANGE]: CUSTOM_TAG_COLOR.WARNING,
  [CustomTaxonomyColor.TAXONOMY_YELLOW]: CUSTOM_TAG_COLOR.CAUTION,
  [CustomTaxonomyColor.TAXONOMY_GREEN]: CUSTOM_TAG_COLOR.SUCCESS,
  [CustomTaxonomyColor.TAXONOMY_BLUE]: CUSTOM_TAG_COLOR.INFO,
  [CustomTaxonomyColor.TAXONOMY_PURPLE]: CUSTOM_TAG_COLOR.ALERT,
  [CustomTaxonomyColor.SANDSTONE]: CUSTOM_TAG_COLOR.SANDSTONE,
  [CustomTaxonomyColor.MINOS]: CUSTOM_TAG_COLOR.MINOS,
};
