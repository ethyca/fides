import { useMemo } from "react";

import { useFeatures } from "~/features/common/features";
import { useGetCustomTaxonomiesQuery } from "~/features/taxonomy/taxonomy.slice";

import {
  BUILT_IN_TAXONOMY_KEYS,
  BUILT_IN_TAXONOMY_LABELS,
  ConditionProperty,
} from "../types";

export interface PolicyTaxonomyOption {
  value: string;
  label: string;
}

export interface PolicyTaxonomyOptionGroup {
  label: string;
  options: PolicyTaxonomyOption[];
}

export interface UsePolicyTaxonomyOptionsResult {
  /** Grouped options ready for an Antd Select. */
  groupedOptions: PolicyTaxonomyOptionGroup[];
  /** Flat list of all valid taxonomy keys (for membership checks). */
  allKeys: string[];
  /** Map of taxonomy key → display label. Falls back to the key when unknown. */
  labelByKey: Record<string, string>;
  isLoading: boolean;
}

/**
 * Single source of truth for the taxonomies selectable in an access policy
 * condition: the 3 core built-ins plus `system_group` (Plus only) plus every
 * custom taxonomy (Plus only). No `applies_to` filtering — every custom
 * taxonomy is offered regardless of which entity types it claims to apply to.
 */
export const usePolicyTaxonomyOptions = (): UsePolicyTaxonomyOptionsResult => {
  const features = useFeatures();
  const isPlusEnabled = features.plus;

  const { data: customTaxonomies = [], isLoading: isLoadingCustom } =
    useGetCustomTaxonomiesQuery(undefined, { skip: !isPlusEnabled });

  return useMemo(() => {
    const builtInKeys = BUILT_IN_TAXONOMY_KEYS.filter(
      (key) => key !== ConditionProperty.SYSTEM_GROUP || isPlusEnabled,
    );

    const builtInOptions: PolicyTaxonomyOption[] = builtInKeys.map((key) => ({
      value: key,
      label: BUILT_IN_TAXONOMY_LABELS[key],
    }));

    const reservedKeys = new Set<string>(builtInKeys);
    const customOptions: PolicyTaxonomyOption[] = customTaxonomies
      .filter((t) => !reservedKeys.has(t.fides_key))
      .map((t) => ({
        value: t.fides_key,
        label: t.name || t.fides_key,
      }));

    const groupedOptions: PolicyTaxonomyOptionGroup[] = [
      { label: "Built-in", options: builtInOptions },
    ];
    if (customOptions.length > 0) {
      groupedOptions.push({ label: "Custom", options: customOptions });
    }

    const labelByKey: Record<string, string> = {};
    builtInOptions.forEach((o) => {
      labelByKey[o.value] = o.label;
    });
    customOptions.forEach((o) => {
      labelByKey[o.value] = o.label;
    });

    return {
      groupedOptions,
      allKeys: [
        ...builtInOptions.map((o) => o.value),
        ...customOptions.map((o) => o.value),
      ],
      labelByKey,
      isLoading: isLoadingCustom,
    };
  }, [customTaxonomies, isLoadingCustom, isPlusEnabled]);
};
