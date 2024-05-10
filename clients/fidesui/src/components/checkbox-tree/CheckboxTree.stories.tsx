import { Box, Heading, Stack } from "@fidesui/react";
import React, { useState } from "react";

import { CheckboxTree } from "./CheckboxTree";

export default {
  title: "Components/CheckboxTree",
  component: CheckboxTree,
};

const MOCK_NODES = [
  {
    label: "grandparent",
    value: "grandparent",
    children: [
      {
        label: "parent",
        value: "grandparent.parent",
        children: [
          { label: "child", value: "grandparent.parent.child", children: [] },
          {
            label: "sibling",
            value: "grandparent.parent.sibling",
            children: [],
          },
        ],
      },
      {
        label: "aunt",
        value: "grandparent.aunt",
        children: [],
      },
      {
        label: "aunt_second",
        value: "grandparent.aunt_second",
        children: [],
      },
    ],
  },
  {
    label: "great uncle",
    value: "great uncle",
    children: [],
  },
] as const;

export const CheckboxTreeStory = () => {
  const [selected, setSelected] = useState<string[]>([]);
  return (
    <Stack>
      <Heading size="md">The Checkbox Tree</Heading>
      <Box maxW="50%" bg="white" borderRadius="md">
        <CheckboxTree
          nodes={MOCK_NODES}
          selected={selected}
          onSelected={setSelected}
        />
      </Box>
      <Heading size="md">Selected:</Heading>
      <pre>{selected.join(", ") || "None"}</pre>
    </Stack>
  );
};
