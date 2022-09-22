import { Box, ButtonProps } from "@fidesui/react";
import { MultiValue, Select } from "chakra-react-select";

import { DataCategory } from "~/types/api";

import {
  DataCategoryDropdown,
  Props as DataCategoryDropdownProps,
} from "./DataCategoryInput";

// TODO: just making up a structure until we have something real from the API
interface DataCategoryWithConfidence extends DataCategory {
  confidence: number;
}

interface Props extends DataCategoryDropdownProps {
  mostLikelyCategories: DataCategoryWithConfidence[];
}

const ClassifiedDataCategoryInput = ({
  mostLikelyCategories,
  onChecked,
  checked,
  ...props
}: Props) => {
  const menuButtonProps: ButtonProps = {
    size: "sm",
    colorScheme: "complimentary",
    borderRadius: "6px 0px 0px 6px",
  };

  const options = mostLikelyCategories
    .sort((a, b) => b.confidence - a.confidence)
    .map((c) => ({
      label: `${c.name} (${c.confidence}%)`,
      value: c.fides_key,
    }));

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
          {...props}
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

export default ClassifiedDataCategoryInput;
