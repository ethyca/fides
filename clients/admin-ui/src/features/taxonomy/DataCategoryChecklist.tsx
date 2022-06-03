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
  const [checked, setChecked] = useState<string[]>(["account"]);
  return (
    <CheckboxTree nodes={nodes} checked={checked} onChecked={setChecked} />
  );
};

export default DataCategoryChecklist;
