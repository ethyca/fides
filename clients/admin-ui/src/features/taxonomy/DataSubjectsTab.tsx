import { Spinner, Text } from "@fidesui/react";

import { useGetAllDataSubjectsQuery } from "~/features/data-subjects/data-subject.slice";

const useDataSubjects = () => {
  const { data, isLoading } = useGetAllDataSubjectsQuery();

  return {
    isLoading,
    dataSubjects: data,
  };
};

const DataSubjectsTab = () => {
  const { isLoading, dataSubjects } = useDataSubjects();
  if (isLoading) {
    return <Spinner />;
  }
  if (!dataSubjects) {
    return <Text>Could not find data subjects.</Text>;
  }

  // TODO: Build actual component, just render data simply for now (#853)
  return (
    <>
      {dataSubjects.map((ds) => (
        <Text key={ds.fides_key}>{ds.name}</Text>
      ))}
    </>
  );
};

export default DataSubjectsTab;
