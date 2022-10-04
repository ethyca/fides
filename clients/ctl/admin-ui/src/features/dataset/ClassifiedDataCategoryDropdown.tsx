import { Box, ButtonProps } from "@fidesui/react";
import { MultiValue, Select } from "chakra-react-select";
import { useMemo } from "react";

import { DataCategory } from "~/types/api";

import DataCategoryDropdown from "./DataCategoryDropdown";
import { DataCategoryWithConfidence } from "./types";

interface Props {
  dataCategories: DataCategory[];
  mostLikelyCategories: DataCategoryWithConfidence[];
  checked: string[];
  onChecked: (newChecked: string[]) => void;
}

const ClassifiedDataCategoryDropdown = ({
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

  const allCategoriesWithConfidence = useMemo(
    () =>
      dataCategories.map((dc) => {
        const categoryWithConfidence = mostLikelyCategories.find(
          (mlc) => mlc.fides_key === dc.fides_key
        );
        if (categoryWithConfidence) {
          return categoryWithConfidence;
        }
        return { ...dc, confidence: undefined };
      }),
    [mostLikelyCategories, dataCategories]
  );

  const options = allCategoriesWithConfidence
    .sort((a, b) => {
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
    })
    .map((c) => {
      const confidence =
        c.confidence === undefined
          ? "N/A"
          : `${(c.confidence * 100).toFixed()}%`;
      return {
        label: `${c.fides_key} (${confidence})`,
        value: c.fides_key,
      };
    });

  const selectedOptions = options.filter((o) => checked.indexOf(o.value) >= 0);

  const handleChange = (
    newValues: MultiValue<{ label: string; value: string }>
  ) => {
    const oldKeys = selectedOptions.map((o) => o.value);
    const newKeys = newValues.map((o) => o.value);
    let newChecked;

    if (newKeys.length > oldKeys.length) {
      const addedKey = newKeys.filter(
        (newKey) => oldKeys.indexOf(newKey) === -1
      )[0];
      newChecked = [...checked, addedKey];
    } else {
      const removedKey = oldKeys.filter(
        (oldKey) => newKeys.indexOf(oldKey) === -1
      )[0];
      newChecked = checked.filter((c) => c !== removedKey);
    }
    onChecked(newChecked);
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
