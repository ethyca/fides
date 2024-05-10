import { Box, Heading, ListItem, OrderedList, Stack } from "@fidesui/react";
import React, { useState } from "react";

import { MOCK_DATA_CATEGORIES } from "../mock-data";
import { ClassifiedDataCategoryDropdown } from "./ClassifiedDataCategoryDropdown";

export default {
  title: "Components/ClassifiedDataCategoryDropdown",
  component: ClassifiedDataCategoryDropdown,
};

const MOST_LIKELY_CATEGORIES = MOCK_DATA_CATEGORIES.slice(0, 5).map((c) => ({
  ...c,
  confidence: Math.random(),
}));

const ClassifiedDataCategoryDropdownStory = ({
  initialChecked,
}: {
  initialChecked: string[];
}) => {
  const [checked, setChecked] = useState<string[]>(initialChecked);

  return (
    <Stack>
      <Heading size="md">Data Category Dropdown</Heading>
      <Box maxW={600} bg="white" borderRadius="md" p={5}>
        <ClassifiedDataCategoryDropdown
          dataCategories={MOCK_DATA_CATEGORIES}
          mostLikelyCategories={MOST_LIKELY_CATEGORIES}
          checked={checked}
          onChecked={setChecked}
        />
      </Box>
      <Heading size="md">Selected: {checked.length}</Heading>
      <Box>
        <OrderedList>
          {checked.map((key) => (
            <ListItem>
              <pre>
                {key}
                {MOST_LIKELY_CATEGORIES.find((c) => c.fides_key === key)
                  ? " (classified)"
                  : " (from taxonomy)"}
              </pre>
            </ListItem>
          ))}
        </OrderedList>
      </Box>
    </Stack>
  );
};

export const WithNothingSelected = () => (
  <ClassifiedDataCategoryDropdownStory initialChecked={[]} />
);

export const WithTaxonomySelection = () => (
  <ClassifiedDataCategoryDropdownStory
    initialChecked={[
      MOST_LIKELY_CATEGORIES[0].fides_key,
      MOCK_DATA_CATEGORIES[5].fides_key,
    ]}
  />
);
