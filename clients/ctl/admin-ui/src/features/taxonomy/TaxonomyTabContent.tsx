import {
  Center,
  SimpleGrid,
  Spinner,
  Text,
  useDisclosure,
} from "@fidesui/react";
import { useMemo, useState } from "react";

import ConfirmationModal from "~/features/common/ConfirmationModal";

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
    onEdit,
    onDelete,
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
  const [deleteKey, setDeleteKey] = useState<string | null>(null);

  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

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

  const handleSetDeleteKey = (node: TaxonomyEntityNode) => {
    setDeleteKey(node.value);
    onDeleteOpen();
  };

  const handleDelete = () => {
    if (deleteKey) {
      onDelete(deleteKey);
      onDeleteClose();
    }
  };

  return (
    <>
      <SimpleGrid columns={2} spacing={2}>
        <AccordionTree
          nodes={taxonomyNodes}
          onEdit={handleSetEditEntity}
          onDelete={handleSetDeleteKey}
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
      <ConfirmationModal
        isOpen={deleteIsOpen}
        onClose={onDeleteClose}
        onConfirm={handleDelete}
        title={`Delete ${labels.fides_key.toLocaleLowerCase()}`}
        message={
          <Text>
            You are about to permanently delete the{" "}
            {labels.fides_key.toLocaleLowerCase()}{" "}
            <Text color="complimentary.500" as="span" fontWeight="bold">
              {deleteKey}
            </Text>{" "}
            from your taxonomy. Are you sure you would like to continue?
          </Text>
        }
      />
    </>
  );
};

export default TaxonomyTabContent;
