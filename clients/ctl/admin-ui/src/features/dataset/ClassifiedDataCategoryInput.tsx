import { Box, ButtonProps } from "@fidesui/react";
import { Select } from "chakra-react-select";

import { DataCategory } from "~/types/api";

import {
  DataCategoryDropdown,
  DataCategoryDropdownProps,
} from "./DataCategoryInput";

interface DataCategoryWithConfidence extends DataCategory {
  confidence: number;
}

interface Props extends DataCategoryDropdownProps {
  mostLikelyCategories: DataCategoryWithConfidence[];
}

const ClassifiedDataCategoryInput = ({
  mostLikelyCategories,
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

  return (
    <Box display="flex">
      <Box>
        <DataCategoryDropdown
          {...props}
          buttonProps={menuButtonProps}
          buttonLabel="Search taxonomy"
        />
      </Box>
      <Box>
        <Select
          options={options}
          onChange={(newValue) => {
            console.log({ newValue });
          }}
          value={options}
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
