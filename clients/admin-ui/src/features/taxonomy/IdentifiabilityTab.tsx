import { Spinner, Text } from "@fidesui/react";

import { useGetAllDataQualifiersQuery } from "~/features/data-qualifier/data-qualifier.slice";

const useDataQualifiers = () => {
  const { data, isLoading } = useGetAllDataQualifiersQuery();

  return {
    isLoading,
    dataQualifiers: data,
  };
};

const IdentifiabilityTab = () => {
  const { isLoading, dataQualifiers } = useDataQualifiers();
  if (isLoading) {
    return <Spinner />;
  }
  if (!dataQualifiers) {
    return <Text>Could not find data categories.</Text>;
  }

  // TODO: Build actual component, just render data simply for now (#853)
  return (
    <>
      {dataQualifiers.map((dq) => (
        <Text key={dq.fides_key}>{dq.name}</Text>
      ))}
    </>
  );
};

export default IdentifiabilityTab;
