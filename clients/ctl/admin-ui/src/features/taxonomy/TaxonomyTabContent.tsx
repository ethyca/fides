import { Center, SimpleGrid, Spinner, Text } from "@fidesui/react";
import { useEffect, useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";

import AccordionTree from "../common/AccordionTree";
import { transformTaxonomyEntityToNodes } from "./helpers";
import { TaxonomyHookData } from "./hooks";
import { selectAddTaxonomyType, setAddTaxonomyType } from "./taxonomy.slice";
import TaxonomyFormBase from "./TaxonomyFormBase";
import { TaxonomyEntity, TaxonomyEntityNode } from "./types";

interface Props {
  useTaxonomy: () => TaxonomyHookData<TaxonomyEntity>;
}

const DEFAULT_INITIAL_VALUES: TaxonomyEntity = {
  fides_key: "",
  parent_key: "",
  name: "",
  description: "",
};

const TaxonomyTabContent = ({ useTaxonomy }: Props) => {
  const dispatch = useAppDispatch();
  const {
    isLoading,
    data,
    labels,
    edit: onEdit,
    onCreate,
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
  const addTaxonomyType = useAppSelector(selectAddTaxonomyType);

  useEffect(() => {
    if (addTaxonomyType) {
      setEditEntity(null);
    }
  }, [addTaxonomyType]);

  const closeAddForm = () => {
    dispatch(setAddTaxonomyType(null));
  };

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
    if (addTaxonomyType) {
      closeAddForm();
    }
    const entity = data?.find((d) => d.fides_key === node.value) ?? null;
    setEditEntity(entity);
  };

  const handleCreate = (entity: TaxonomyEntity) => onCreate(entity);

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
          onCancel={() => setEditEntity(null)}
          onSubmit={onEdit}
          extraFormFields={extraFormFields}
          initialValues={transformEntityToInitialValues(editEntity)}
        />
      ) : null}
      {addTaxonomyType ? (
        <TaxonomyFormBase
          labels={labels}
          onCancel={closeAddForm}
          onSubmit={handleCreate}
          extraFormFields={extraFormFields}
          initialValues={transformEntityToInitialValues(DEFAULT_INITIAL_VALUES)}
          isCreate
        />
      ) : null}
    </SimpleGrid>
  );
};

export default TaxonomyTabContent;
