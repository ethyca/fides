import { Box, Heading, Text } from "@fidesui/react";
import { useMemo } from "react";

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
  return (
    <Box>
      <Heading size="md" mb={2}>
        🚧 In progress 🚧
      </Heading>
      {nodes.map((n) => (
        <Text key={n.value}>{n.label}</Text>
      ))}
    </Box>
  );
};

export default DataCategoryChecklist;
