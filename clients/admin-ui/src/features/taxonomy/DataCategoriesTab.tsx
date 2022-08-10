import { useDataCategory } from "./hooks";
import TaxonomyTabContent from "./TaxonomyTabContent";

const DataCategoriesTab = () => {
  const { isLoading, data, labels, edit } = useDataCategory();
  return (
    <TaxonomyTabContent
      isLoading={isLoading}
      data={data}
      labels={labels}
      edit={edit}
    />
  );
};

export default DataCategoriesTab;
