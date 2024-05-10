import { Box, Heading, HStack, Stack } from "@fidesui/react";
import React, { useState } from "react";

import { ColumnDropdown, ColumnMetadata } from "./ColumnDropdown";

export default {
  title: "Components/ColumnDropdown",
  component: ColumnDropdown,
};

export const ColumnDropdownStory = () => {
  const [columns, setColumns] = useState<ColumnMetadata[]>([]);
  return (
    <Stack>
      <Heading size="md">Column Dropdown</Heading>
      <HStack spacing={5}>
        <Box maxW="50%">
          <ColumnDropdown
            allColumns={[
              { name: "Key", attribute: "fides_key" },
              { name: "Description", attribute: "description" },
              { name: "Service type", attribute: "service_type" },
            ]}
            selectedColumns={columns}
            onChange={setColumns}
          />
        </Box>
        <Box>
          <Heading size="md">Selected attributes:</Heading>
          <pre>{columns.map((c) => c.attribute).join(", ") || "None"}</pre>
        </Box>
      </HStack>
    </Stack>
  );
};
