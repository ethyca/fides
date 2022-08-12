import { useGetAllDataCategoriesQuery } from "./data-categories.slice";
import TaxonomyTabContent from "./TaxonomyTabContent";

const useDataCategories = () => {
  const { data, isLoading } = useGetAllDataCategoriesQuery();

  return {
    isLoading,
    dataCategories: data,
  };
};

const DataCategoriesTab = () => {
  const { isLoading, dataCategories } = useDataCategories();
  return <TaxonomyTabContent isLoading={isLoading} data={dataCategories} />;
};

export default DataCategoriesTab;
