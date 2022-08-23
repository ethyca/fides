import { Center, SimpleGrid, Spinner, Text } from "@fidesui/react";
import { useMemo, useState } from "react";

import AccordionTree from "../common/AccordionTree";
import { transformTaxonomyEntityToNodes } from "./helpers";
import { TaxonomyHookData } from "./hooks";
import TaxonomyFormBase from "./TaxonomyFormBase";
import { TaxonomyEntity, TaxonomyEntityNode } from "./types";

interface Props {
  useTaxonomy: () => TaxonomyHookData<TaxonomyEntity>;
}

const TaxonomyTabContent = ({ useTaxonomy }: Props) => {
  const {
    isLoading,
    data,
    labels,
    edit: onEdit,
    extraFormFields,
    transformEntityToInitialValues,
  } = useTaxonomy();
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
        <TaxonomyFormBase
          labels={labels}
          entity={editEntity}
          onCancel={() => setEditEntity(null)}
          onEdit={onEdit}
          extraFormFields={extraFormFields}
          initialValues={transformEntityToInitialValues(editEntity)}
        />
      ) : null}
    </SimpleGrid>
  );
};

export default TaxonomyTabContent;
