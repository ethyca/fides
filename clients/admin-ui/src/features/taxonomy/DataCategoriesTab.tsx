import { Spinner, Text } from "@fidesui/react";

import { useGetAllDataCategoriesQuery } from "./data-categories.slice";

const useDataCategories = () => {
  const { data, isLoading } = useGetAllDataCategoriesQuery();

  return {
    isLoading,
    dataCategories: data,
  };
};

const DataCategoriesTab = () => {
  const { isLoading, dataCategories } = useDataCategories();
  if (isLoading) {
    return <Spinner />;
  }
  if (!dataCategories) {
    return <Text>Could not find data categories.</Text>;
  }

  // TODO: Build actual component, just render data simply for now (#853)
  return (
    <>
      {dataCategories.map((dc) => (
        <Text key={dc.fides_key}>{dc.name}</Text>
      ))}
    </>
  );
};

export default DataCategoriesTab;
