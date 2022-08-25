import {
  Center,
  SimpleGrid,
  Spinner,
  Text,
  useDisclosure,
  useToast,
} from "@fidesui/react";
import { useMemo, useState } from "react";

import AccordionTree from "~/features/common/AccordionTree";
import ConfirmationModal from "~/features/common/ConfirmationModal";
import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { isErrorResult } from "~/types/errors";

import ActionButtons from "./ActionButtons";
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
    handleEdit,
    handleDelete: deleteEntity,
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
  const toast = useToast();

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

  const taxonomyType = labels.fides_key.toLocaleLowerCase();

  const handleSetEditEntity = (node: TaxonomyEntityNode) => {
    const entity = data?.find((d) => d.fides_key === node.value) ?? null;
    setEditEntity(entity);
  };

  const handleSetDeleteKey = (node: TaxonomyEntityNode) => {
    setDeleteKey(node.value);
    onDeleteOpen();
  };

  const handleDelete = async () => {
    if (deleteKey) {
      const result = await deleteEntity(deleteKey);
      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
      } else {
        toast(successToastParams(`Successfully deleted ${taxonomyType}`));
      }
      onDeleteClose();
      setEditEntity(null);
    }
  };

  return (
    <>
      <SimpleGrid columns={2} spacing={2}>
        <AccordionTree
          nodes={taxonomyNodes}
          focusedKey={editEntity?.fides_key}
          renderHover={(node) => (
            <ActionButtons
              onDelete={handleSetDeleteKey}
              onEdit={handleSetEditEntity}
              node={node}
            />
          )}
        />
        {editEntity ? (
          <TaxonomyFormBase
            labels={labels}
            entity={editEntity}
            onCancel={() => setEditEntity(null)}
            onEdit={handleEdit}
            extraFormFields={extraFormFields}
            initialValues={transformEntityToInitialValues(editEntity)}
          />
        ) : null}
      </SimpleGrid>
      <ConfirmationModal
        isOpen={deleteIsOpen}
        onClose={onDeleteClose}
        onConfirm={handleDelete}
        title={`Delete ${taxonomyType}`}
        message={
          <Text>
            You are about to permanently delete the {taxonomyType}{" "}
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
