import {
  Center,
  SimpleGrid,
  Spinner,
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
import { TreeNode } from "~/features/common/types";
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
    handleCreate: createEntity,
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

  const isAdding = useAppSelector(selectIsAddFormOpen);

  useEffect(() => {
    // prevent both the add and edit forms being opened at once
    if (isAdding) {
      setEditEntity(null);
    }
  }, [isAdding]);

  const closeAddForm = () => {
    dispatch(setIsAddFormOpen(false));
  };

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

  const handleSetEditEntity = (node: TreeNode) => {
    if (isAdding) {
      closeAddForm();
    }
    const entity = data?.find((d) => d.fides_key === node.value) ?? null;
    setEditEntity(entity);
  };

  const handleSetDeleteKey = (node: TreeNode) => {
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
              node={node as TaxonomyEntityNode}
            />
          )}
          renderTag={(node) => <CustomTag node={node as TaxonomyEntityNode} />}
        />
        {editEntity ? (
          <TaxonomyFormBase
            labels={labels}
            onCancel={() => setEditEntity(null)}
            onSubmit={handleEdit}
            extraFormFields={extraFormFields}
            initialValues={transformEntityToInitialValues(editEntity)}
          />
        ) : null}
        {isAdding ? (
          <TaxonomyFormBase
            labels={labels}
            onCancel={closeAddForm}
            onSubmit={createEntity}
            extraFormFields={extraFormFields}
            initialValues={transformEntityToInitialValues(
              DEFAULT_INITIAL_VALUES
            )}
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
