import { Box, SimpleGrid, Text } from "@fidesui/react";
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
  const [checked, setChecked] = useState<string[]>([]);

  return (
    <SimpleGrid columns={[2]}>
      <CheckboxTree nodes={nodes} checked={checked} onChecked={setChecked} />
      <Box>
        <Text fontWeight="semibold">Selected</Text>
        {checked.map((c) => (
          <Text key={c}>{c}</Text>
        ))}
      </Box>
    </SimpleGrid>
  );
};

export default DataCategoryChecklist;
