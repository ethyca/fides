import { Select, Tag } from "fidesui";
import type { CustomTagProps } from "rc-select/lib/BaseSelect";
import { useMemo } from "react";

const SEPARATOR = "::";

interface FacetDefinition {
  key: string;
  label: string;
  options: string[];
}

interface FacetedSearchInputProps {
  facets: FacetDefinition[];
  value: string[];
  onChange: (value: string[]) => void;
}

const FacetedSearchInput = ({
  facets,
  value,
  onChange,
}: FacetedSearchInputProps) => {
  const groupedOptions = useMemo(
    () =>
      facets.map((facet) => ({
        label: facet.label,
        options: facet.options.map((option) => ({
          label: option,
          value: `${facet.key}${SEPARATOR}${option}`,
        })),
      })),
    [facets],
  );

  const tagRender = (props: CustomTagProps) => {
    const { label: tagLabel, value: tagValue, closable, onClose } = props;
    const facetKey = String(tagValue).split(SEPARATOR)[0];
    const facet = facets.find((f) => f.key === facetKey);
    return (
      <Tag closable={closable} onClose={onClose} className="my-0.5 mr-1.5">
        {facet ? <strong>{facet.label}: </strong> : null}
        {tagLabel}
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
      className="w-full [&_.ant-select-selection-overflow]:gap-1"
    />
  );
};

export { FacetedSearchInput, SEPARATOR };
export type { FacetDefinition };
