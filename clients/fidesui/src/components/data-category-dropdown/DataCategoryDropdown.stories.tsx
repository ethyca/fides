import { Box, Heading, Stack } from "@fidesui/react";
import React, { useState } from "react";

import { MOCK_DATA_CATEGORIES } from "../mock-data";
import { DataCategoryDropdown } from "./DataCategoryDropdown";

export default {
  title: "Components/DataCategoryDropdown",
  component: DataCategoryDropdown,
};

export const DataCategoryDropdownStory = () => {
  const [checked, setChecked] = useState<string[]>([]);
  return (
    <Stack>
      <Heading size="md">Data Category Dropdown</Heading>
      <Box maxW="50%" bg="white" borderRadius="md">
        <DataCategoryDropdown
          dataCategories={MOCK_DATA_CATEGORIES}
          checked={checked}
          onChecked={setChecked}
        />
      </Box>
      <Heading size="md">Selected:</Heading>
      <pre>{checked.join(", ") || "None"}</pre>
    </Stack>
  );
};
