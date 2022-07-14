import { Spinner, Text } from "@fidesui/react";

import { useGetAllDataUsesQuery } from "~/features/data-use/data-use.slice";

const useDataCategories = () => {
  const { data, isLoading } = useGetAllDataUsesQuery();

  return {
    isLoading,
    dataUses: data,
  };
};

const DataUsesTab = () => {
  const { isLoading, dataUses } = useDataCategories();
  if (isLoading) {
    return <Spinner />;
  }
  if (!dataUses) {
    return <Text>Could not find data uses.</Text>;
  }

  // TODO: Build actual component, just render data simply for now (#853)
  return (
    <>
      {dataUses.map((du) => (
        <Text key={du.fides_key}>{du.name}</Text>
      ))}
    </>
  );
};

export default DataUsesTab;
