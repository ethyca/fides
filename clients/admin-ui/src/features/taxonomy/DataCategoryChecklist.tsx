import { Box, Heading, SimpleGrid, Text } from "@fidesui/react";
import { useMemo, useState } from "react";

import CheckboxTree from "../common/CheckboxTree";
import { transformDataCategoriesToNodes } from "./helpers";
import { DataCategory } from "./types";

interface Props {
  dataCategories: DataCategory[];
}
const DataCategoryChecklist = ({ dataCategories }: Props) => {
  const nodes = useMemo(
    () => transformDataCategoriesToNodes(dataCategories),
    [dataCategories]
  );
  const [checked, setChecked] = useState<string[]>(["account.contact.city"]);

  return (
    <Box>
      <Box backgroundColor="peachpuff" p={2} mb={4}>
        <Heading size="sm" textAlign="center">
          🚧 In progress 🚧
        </Heading>
      </Box>
      <SimpleGrid columns={[2]}>
        <CheckboxTree
          nodes={nodes}
          selected={checked}
          onSelected={setChecked}
        />
        <Box>
          <Text fontWeight="semibold">Selected</Text>
          {checked.map((c) => (
            <Text key={c}>{c}</Text>
          ))}
        </Box>
      </SimpleGrid>
    </Box>
  );
};

export default DataCategoryChecklist;
