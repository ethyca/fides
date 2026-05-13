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

export interface UsePolicyTaxonomyOptionsResult {
  /** Flat options list — built-ins first, then custom taxonomies. */
  options: PolicyTaxonomyOption[];
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

    const options = [...builtInOptions, ...customOptions];

    const labelByKey: Record<string, string> = {};
    options.forEach((o) => {
      labelByKey[o.value] = o.label;
    });

    return {
      options,
      labelByKey,
      isLoading: isLoadingCustom,
    };
  }, [customTaxonomies, isLoadingCustom, isPlusEnabled]);
};
