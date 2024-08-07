import { MultiValue, Select } from "chakra-react-select";
import { Box, ButtonProps } from "fidesui";
import React, { useMemo } from "react";

import { DataCategoryDropdown } from "../data-category-dropdown";
import { DataCategory } from "../types/api";
import { DataCategoryWithConfidence } from "./types";

interface Props {
  dataCategories: DataCategory[];
  mostLikelyCategories: DataCategoryWithConfidence[];
  checked: string[];
  onChecked: (newChecked: string[]) => void;
}

export const ClassifiedDataCategoryDropdown = ({
  mostLikelyCategories,
  onChecked,
  checked,
  dataCategories,
}: Props) => {
  const menuButtonProps: ButtonProps = {
    size: "sm",
    colorScheme: "complimentary",
    borderRadius: "6px 0px 0px 6px",
  };

  const mostLikelySorted = useMemo(
    () =>
      mostLikelyCategories.sort((a, b) => {
        if (a.confidence !== undefined && b.confidence !== undefined) {
          return b.confidence - a.confidence;
        }
        if (a.confidence === undefined) {
          return 1;
        }
        if (b.confidence === undefined) {
          return -1;
        }
        return a.fides_key.localeCompare(b.fides_key);
      }),
    [mostLikelyCategories],
  );

  const options = useMemo(
    () =>
      mostLikelySorted.map((c) => ({
        label: c.fides_key,
        value: c.fides_key,
      })),
    [mostLikelySorted],
  );

  const selectedOptions = useMemo(
    () =>
      checked.map((key) => ({
        label: key,
        value: key,
      })),
    [checked],
  );

  const handleChange = (
    newValues: MultiValue<{ label: string; value: string }>,
  ) => {
    onChecked(newValues.map((o) => o.value));
  };

  return (
    <Box display="flex">
      <Box>
        <DataCategoryDropdown
          dataCategories={dataCategories}
          checked={checked}
          onChecked={onChecked}
          buttonProps={menuButtonProps}
          buttonLabel="Search taxonomy"
        />
      </Box>
      <Box flexGrow={1} data-testid="classified-select">
        <Select
          options={options}
          onChange={handleChange}
          value={selectedOptions}
          size="sm"
          placeholder="Select from recommendations..."
          chakraStyles={{
            dropdownIndicator: (provided) => ({
              ...provided,
              bg: "transparent",
              px: 2,
              cursor: "inherit",
            }),
            indicatorSeparator: (provided) => ({
              ...provided,
              display: "none",
            }),
            multiValue: (provided) => ({
              ...provided,
              background: "primary.400",
              color: "white",
            }),
          }}
          components={{
            ClearIndicator: () => null,
          }}
          isSearchable
          isClearable
          isMulti
          instanceId="classified-data-category-input-multiselect"
        />
      </Box>
    </Box>
  );
};

export default ClassifiedDataCategoryDropdown;
