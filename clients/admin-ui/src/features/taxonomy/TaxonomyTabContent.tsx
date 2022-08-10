import { Center, SimpleGrid, Spinner, Text } from "@fidesui/react";
import { useMemo, useState } from "react";

import AccordionTree from "../common/AccordionTree";
import EditTaxonomyForm from "./EditTaxonomyForm";
import { transformTaxonomyEntityToNodes } from "./helpers";
import { TaxonomyEntity, TaxonomyEntityNode } from "./types";

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

  const [editEntity, setEditEntity] = useState<TaxonomyEntity | null>(null);

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

  const handleEdit = (node: TaxonomyEntityNode) => {
    const entity = data?.find((d) => d.fides_key === node.value) ?? null;
    setEditEntity(entity);
  };

  return (
    <SimpleGrid columns={2} spacing={2}>
      <AccordionTree
        nodes={taxonomyNodes}
        onEdit={handleEdit}
        focusedKey={editEntity?.fides_key}
      />
      {editEntity ? (
        <EditTaxonomyForm
          entity={editEntity}
          onCancel={() => setEditEntity(null)}
        />
      ) : null}
    </SimpleGrid>
  );
};

export default TaxonomyTabContent;
