import { CustomTaxonomyColor } from "~/types/api";

export const COLOR_VALUE_MAP: Record<CustomTaxonomyColor, string> = {
  [CustomTaxonomyColor.TAXONOMY_WHITE]: "default",
  [CustomTaxonomyColor.TAXONOMY_RED]: "error",
  [CustomTaxonomyColor.TAXONOMY_ORANGE]: "warning",
  [CustomTaxonomyColor.TAXONOMY_YELLOW]: "caution",
  [CustomTaxonomyColor.TAXONOMY_GREEN]: "success",
  [CustomTaxonomyColor.TAXONOMY_BLUE]: "info",
  [CustomTaxonomyColor.TAXONOMY_PURPLE]: "alert",
  [CustomTaxonomyColor.SANDSTONE]: "sandstone",
  [CustomTaxonomyColor.MINOS]: "minos",
};
