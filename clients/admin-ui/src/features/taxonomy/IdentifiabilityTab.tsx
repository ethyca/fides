import { useGetAllDataQualifiersQuery } from "~/features/data-qualifier/data-qualifier.slice";

import TaxonomyTabContent from "./TaxonomyTabContent";

const useDataQualifiers = () => {
  const { data, isLoading } = useGetAllDataQualifiersQuery();

  return {
    isLoading,
    dataQualifiers: data,
  };
};

const IdentifiabilityTab = () => {
  const { isLoading, dataQualifiers } = useDataQualifiers();
  return <TaxonomyTabContent isLoading={isLoading} data={dataQualifiers} />;
};

export default IdentifiabilityTab;
