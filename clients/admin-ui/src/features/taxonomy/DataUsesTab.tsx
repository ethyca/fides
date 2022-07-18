import { useGetAllDataUsesQuery } from "~/features/data-use/data-use.slice";

import TaxonomyTabContent from "./TaxonomyTabContent";

const useDataCategories = () => {
  const { data, isLoading } = useGetAllDataUsesQuery();

  return {
    isLoading,
    dataUses: data,
  };
};

const DataUsesTab = () => {
  const { isLoading, dataUses } = useDataCategories();
  return <TaxonomyTabContent isLoading={isLoading} data={dataUses} />;
};

export default DataUsesTab;
