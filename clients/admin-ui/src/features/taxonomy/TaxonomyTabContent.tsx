import { Spinner, Text } from "@fidesui/react";

import { TaxonomyEntity } from "./types";

interface Props {
  isLoading: boolean;
  data: TaxonomyEntity[] | undefined;
}
const TaxonomyTabContent = ({ isLoading, data }: Props) => {
  if (isLoading) {
    return <Spinner />;
  }
  if (!data) {
    return <Text>Could not find data.</Text>;
  }

  // TODO: Build actual component, just render data simply for now (#853)
  return (
    <>
      {data.map((d) => (
        <Text key={d.fides_key}>{d.name}</Text>
      ))}
    </>
  );
};

export default TaxonomyTabContent;
