import { Box, Center, SimpleGrid, Spinner, Text } from "@fidesui/react";
import { useMemo } from "react";

import AccordionTree from "../common/AccordionTree";
import { transformTaxonomyEntityToNodes } from "./helpers";
import { TaxonomyEntity } from "./types";

interface Props {
  isLoading: boolean;
  data: TaxonomyEntity[] | undefined;
}
const TaxonomyTabContent = ({ isLoading, data }: Props) => {
  const taxonomyNodes = useMemo(() => {
    if (data) {
      return transformTaxonomyEntityToNodes(data);
    }
    return null;
  }, [data]);

  if (isLoading) {
    return (
      <Center>
        <Spinner />
      </Center>
    );
  }
  if (!taxonomyNodes) {
    return <Text>Could not find data.</Text>;
  }

  return (
    <SimpleGrid columns={2}>
      <AccordionTree nodes={taxonomyNodes} />
      <Box>Edit form</Box>
    </SimpleGrid>
  );
};

export default TaxonomyTabContent;
