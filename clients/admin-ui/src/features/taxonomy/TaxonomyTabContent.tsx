import { Center, SimpleGrid, Spinner, Text } from "@fidesui/react";
import { useMemo, useState } from "react";

import AccordionTree from "../common/AccordionTree";
import EditTaxonomyForm from "./EditTaxonomyForm";
import { transformTaxonomyEntityToNodes } from "./helpers";
import { Labels, TaxonomyEntity, TaxonomyEntityNode } from "./types";

interface Props {
  isLoading: boolean;
  data: TaxonomyEntity[] | undefined;
  labels: Labels;
  edit: (entity: TaxonomyEntity) => void;
}
const TaxonomyTabContent = ({ isLoading, data, labels, edit }: Props) => {
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

  const handleSetEditEntity = (node: TaxonomyEntityNode) => {
    const entity = data?.find((d) => d.fides_key === node.value) ?? null;
    setEditEntity(entity);
  };

  return (
    <SimpleGrid columns={2} spacing={2}>
      <AccordionTree
        nodes={taxonomyNodes}
        onEdit={handleSetEditEntity}
        focusedKey={editEntity?.fides_key}
      />
      {editEntity ? (
        <EditTaxonomyForm
          labels={labels}
          entity={editEntity}
          onCancel={() => setEditEntity(null)}
          onEdit={edit}
        />
      ) : null}
    </SimpleGrid>
  );
};

export default TaxonomyTabContent;
