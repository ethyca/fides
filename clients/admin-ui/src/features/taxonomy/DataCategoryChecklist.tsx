import { Box } from "@fidesui/react";
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
  console.log({ dataCategories, nodes });
  return <Box>hi</Box>;
};

export default DataCategoryChecklist;
