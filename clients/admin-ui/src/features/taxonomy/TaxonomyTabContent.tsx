import {
  Center,
  SimpleGrid,
  Spinner,
  Stack,
  Tag,
  Text,
  useDisclosure,
  useToast,
} from "@fidesui/react";
import { useEffect, useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import AccordionTree from "~/features/common/AccordionTree";
import ConfirmationModal from "~/features/common/ConfirmationModal";
import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { isErrorResult } from "~/types/errors";

import ActionButtons from "./ActionButtons";
import { transformTaxonomyEntityToNodes } from "./helpers";
import { TaxonomyHookData } from "./hooks";
import { selectIsAddFormOpen, setIsAddFormOpen } from "./taxonomy.slice";
import TaxonomyFormBase from "./TaxonomyFormBase";
import { TaxonomyEntity, TaxonomyEntityNode } from "./types";

const CustomTag = ({ node }: { node: TaxonomyEntityNode }) => {
  const { is_default: isDefault } = node;
  return !isDefault ? (
    <Tag
      backgroundColor="gray.500"
      color="white"
      size="sm"
      height="fit-content"
      data-testid={`custom-tag-${node.label}`}
    >
      Custom
    </Tag>
  ) : null;
};

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
    entityToEdit,
    setEntityToEdit,
    handleCreate: createEntity,
    handleEdit,
    handleDelete: deleteEntity,
    renderExtraFormFields,
    transformEntityToInitialValues,
  } = useTaxonomy();
  const taxonomyNodes = useMemo(() => {
    if (data) {
      return transformTaxonomyEntityToNodes(data);
    }
    return null;
  }, [data]);

  const [nodeToDelete, setNodeToDelete] = useState<TaxonomyEntityNode | null>(
    null
  );

  const isAdding = useAppSelector(selectIsAddFormOpen);

  useEffect(() => {
    // prevent both the add and edit forms being opened at once
    if (isAdding) {
      setEntityToEdit(null);
    }
  }, [isAdding, setEntityToEdit]);

  const closeAddForm = () => {
    dispatch(setIsAddFormOpen(false));
  };

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

  const handleSetEntityToEdit = (node: TaxonomyEntityNode) => {
    if (isAdding) {
      closeAddForm();
    }
    const entity = data?.find((d) => d.fides_key === node.value) ?? null;
    setEntityToEdit(entity);
  };

  const handleSetNodeToDelete = (node: TaxonomyEntityNode) => {
    setNodeToDelete(node);
    onDeleteOpen();
  };

  const handleDelete = async () => {
    if (nodeToDelete) {
      const result = await deleteEntity(nodeToDelete.value);
      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
      } else {
        toast(successToastParams(`Successfully deleted ${taxonomyType}`));
      }
      onDeleteClose();
      setEntityToEdit(null);
    }
  };

  return (
    <>
      <SimpleGrid columns={2} spacing={2}>
        <AccordionTree
          nodes={taxonomyNodes}
          focusedKey={entityToEdit?.fides_key}
          renderHover={(node) => (
            <ActionButtons
              onDelete={handleSetNodeToDelete}
              onEdit={handleSetEntityToEdit}
              node={node as TaxonomyEntityNode}
            />
          )}
          renderTag={(node) => <CustomTag node={node as TaxonomyEntityNode} />}
        />
        {entityToEdit ? (
          <TaxonomyFormBase
            labels={labels}
            onCancel={() => setEntityToEdit(null)}
            onSubmit={handleEdit}
            renderExtraFormFields={renderExtraFormFields}
            initialValues={transformEntityToInitialValues(entityToEdit)}
          />
        ) : null}
        {isAdding ? (
          <TaxonomyFormBase
            labels={labels}
            onCancel={closeAddForm}
            onSubmit={createEntity}
            renderExtraFormFields={renderExtraFormFields}
            initialValues={transformEntityToInitialValues(
              DEFAULT_INITIAL_VALUES
            )}
          />
        ) : null}
      </SimpleGrid>
      {nodeToDelete ? (
        <ConfirmationModal
          isOpen={deleteIsOpen}
          onClose={onDeleteClose}
          onConfirm={handleDelete}
          title={`Delete ${taxonomyType}`}
          message={
            <Stack>
              <Text>
                You are about to permanently delete the {taxonomyType}{" "}
                <Text color="complimentary.500" as="span" fontWeight="bold">
                  {nodeToDelete.value}
                </Text>{" "}
                from your taxonomy. Are you sure you would like to continue?
              </Text>
              {nodeToDelete.children.length ? (
                <Text color="red" data-testid="delete-children-warning">
                  Deleting{" "}
                  <Text as="span" fontWeight="bold">
                    {nodeToDelete.value}
                  </Text>{" "}
                  will also delete all of its children.
                </Text>
              ) : null}
            </Stack>
          }
        />
      ) : null}
    </>
  );
};

export default TaxonomyTabContent;
