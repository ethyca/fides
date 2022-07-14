import { useGetAllDataSubjectsQuery } from "~/features/data-subjects/data-subject.slice";

import TaxonomyTabContent from "./TaxonomyTabContent";

const useDataSubjects = () => {
  const { data, isLoading } = useGetAllDataSubjectsQuery();

  return {
    isLoading,
    dataSubjects: data,
  };
};

const DataSubjectsTab = () => {
  const { isLoading, dataSubjects } = useDataSubjects();
  return <TaxonomyTabContent isLoading={isLoading} data={dataSubjects} />;
};

export default DataSubjectsTab;
