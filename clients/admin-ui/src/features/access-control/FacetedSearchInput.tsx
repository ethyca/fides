import { Select, Tag } from "fidesui";
import { useMemo } from "react";

import type { FacetOption } from "./types";

export const SEPARATOR = "::";
export const MISSING_LABEL = "Missing";

// Static facet labels (the column header in the tag prefix, e.g. "Policy: ").
// Doesn't depend on the cascading-options query so the prefix renders
// correctly even on the first paint or when the selected value isn't in the
// current options list.
const FACET_KEY_LABELS: Record<string, string> = {
  consumer: "Consumer",
  policy: "Policy",
  dataset: "Dataset",
  data_use: "Data use",
  control: "Control",
};

export interface FacetDefinition {
  key: string;
  label: string;
  options: FacetOption[];
}

interface FacetedSearchInputProps {
  facets: FacetDefinition[];
  value: string[];
  onChange: (value: string[]) => void;
}

export const FacetedSearchInput = ({
  facets,
  value,
  onChange,
}: FacetedSearchInputProps) => {
  // Look up the display label for a selected encoded value (`facet::key`).
  // Used by both the dropdown options and the tagRender fallback path.
  const labelLookup = useMemo(() => {
    const map = new Map<string, string>();
    facets.forEach((facet) => {
      facet.options.forEach((option) => {
        map.set(
          `${facet.key}${SEPARATOR}${option.key}`,
          option.label || MISSING_LABEL,
        );
      });
    });
    return map;
  }, [facets]);

  const groupedOptions = useMemo(
    () =>
      facets.map((facet) => ({
        label: facet.label,
        options: facet.options.map((option) => ({
          label: option.label || MISSING_LABEL,
          value: `${facet.key}${SEPARATOR}${option.key}`,
        })),
      })),
    [facets],
  );

  const tagRender = (props: {
    label: React.ReactNode;
    value: string;
    closable: boolean;
    onClose: () => void;
  }) => {
    const { label: tagLabel, value: tagValue, closable, onClose } = props;
    const sepIdx = String(tagValue).indexOf(SEPARATOR);
    const facetKey =
      sepIdx >= 0 ? String(tagValue).slice(0, sepIdx) : String(tagValue);
    const optionKey =
      sepIdx >= 0 ? String(tagValue).slice(sepIdx + SEPARATOR.length) : "";
    const facetLabel = FACET_KEY_LABELS[facetKey];
    // antd's `tagLabel` is what it found in `options` for this value — if it
    // didn't find one, it falls back to passing the raw value back. Treat
    // that case explicitly and look up the label ourselves (or render the
    // raw key as a last resort).
    const isFallbackLabel = tagLabel === tagValue;
    const displayLabel = isFallbackLabel
      ? (labelLookup.get(tagValue) ?? optionKey ?? MISSING_LABEL)
      : tagLabel;
    return (
      <Tag closable={closable} onClose={onClose} className="my-0.5 mr-1.5">
        {facetLabel ? <strong>{facetLabel}: </strong> : null}
        {displayLabel}
      </Tag>
    );
  };

  return (
    <Select
      mode="multiple"
      aria-label="Search violations by facets"
      placeholder="Search by consumer, policy, dataset, data use..."
      value={value}
      onChange={onChange}
      options={groupedOptions}
      tagRender={tagRender}
      showSearch
      filterOption={(input, option) =>
        String(option?.label ?? "")
          .toLowerCase()
          .includes(input.toLowerCase())
      }
      notFoundContent="No search options"
      className="w-full [&_.ant-select-selection-overflow]:gap-1"
    />
  );
};
