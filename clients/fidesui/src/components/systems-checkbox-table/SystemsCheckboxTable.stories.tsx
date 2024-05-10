import { Box, Heading, HStack, Stack } from "@fidesui/react";
import React, { useState } from "react";

import { ColumnDropdown, ColumnMetadata } from "../column-dropdown";
import { System } from "../types/api";
import { SystemsCheckboxTable } from "./SystemsCheckboxTable";

export default {
  title: "Components/SystemsCheckboxTable",
  component: SystemsCheckboxTable,
};

const MOCK_SYSTEMS: System[] = [
  {
    fides_key: "first_system",
    system_type: "database",
    description: "My first system ever!",
    privacy_declarations: [],
    fidesctl_meta: {
      resource_id:
        "arn:aws:rds:us-east-2:123456789012:cluster:example-postgres-cluster",
    },
  },
  {
    fides_key: "second_system",
    system_type: "cloud storage",
    description: "My second system",
    privacy_declarations: [],
    fidesctl_meta: {
      resource_id: "resource 2",
    },
  },
  {
    fides_key: "third_system",
    system_type: "analytics",
    description: "A third system appears!",
    privacy_declarations: [],
    fidesctl_meta: {
      resource_id: "resource 3",
    },
  },
];

export const SystemsCheckboxTableStory = () => {
  const [checked, setChecked] = useState<System[]>([]);
  return (
    <Stack>
      <Heading size="md">Systems checkbox table</Heading>
      <HStack spacing={5}>
        <Box maxW="50%" bg="white" p={5}>
          <SystemsCheckboxTable
            checked={checked}
            allSystems={MOCK_SYSTEMS}
            onChange={setChecked}
            columns={[
              { name: "Fides key", attribute: "fides_key" },
              { name: "System type", attribute: "system_type" },
            ]}
          />
        </Box>
        <Box>
          <Heading size="md">Selected attributes:</Heading>
          <pre>{checked.map((c) => c.fides_key).join(", ") || "None"}</pre>
        </Box>
      </HStack>
    </Stack>
  );
};

export const WithColumnDropdown = () => {
  const [checked, setChecked] = useState<System[]>([]);
  const [columns, setColumns] = useState<ColumnMetadata[]>([]);
  return (
    <Stack>
      <Heading size="md">Systems checkbox table with column dropdown</Heading>
      <HStack spacing={5} alignItems="start">
        <Box zIndex={2}>
          <ColumnDropdown
            allColumns={[
              { name: "Key", attribute: "fides_key" },
              { name: "Description", attribute: "description" },
              { name: "Service type", attribute: "system_type" },
              { name: "Resource ID", attribute: "fidesctl_meta.resource_id" },
            ]}
            selectedColumns={columns}
            onChange={setColumns}
          />
        </Box>
        <Box maxW="50%" bg="white" p={5}>
          <SystemsCheckboxTable
            checked={checked}
            allSystems={MOCK_SYSTEMS}
            onChange={setChecked}
            columns={columns}
          />
        </Box>
        <Box>
          <Heading size="md">Selected systems:</Heading>
          <pre>{checked.map((c) => c.fides_key).join(", ") || "None"}</pre>
        </Box>
      </HStack>
    </Stack>
  );
};

export const WithTableHeadProps = () => {
  const [checked, setChecked] = useState<System[]>([]);
  return (
    <Stack>
      <Heading size="md">Systems checkbox table with styled header</Heading>
      <HStack spacing={5}>
        <Box maxW="50%" bg="white" maxHeight="100px" overflowY="scroll">
          <SystemsCheckboxTable
            checked={checked}
            allSystems={MOCK_SYSTEMS}
            onChange={setChecked}
            columns={[
              { name: "Fides key", attribute: "fides_key" },
              { name: "System type", attribute: "system_type" },
            ]}
            tableHeadProps={{
              bg: "peachpuff",
              position: "sticky",
              top: 0,
              zIndex: 1,
            }}
          />
        </Box>
        <Box>
          <Heading size="md">Selected attributes:</Heading>
          <pre>{checked.map((c) => c.fides_key).join(", ") || "None"}</pre>
        </Box>
      </HStack>
    </Stack>
  );
};
