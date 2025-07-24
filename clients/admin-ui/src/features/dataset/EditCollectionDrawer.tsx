import { errorToastParams, successToastParams } from "common/toast";
import { ConfirmationModal, Text, useDisclosure, useToast } from "fidesui";
import { useMemo } from "react";

import EditDrawer, {
  EditDrawerFooter,
  EditDrawerHeader,
} from "~/features/common/EditDrawer";
import { Dataset, DatasetCollection } from "~/types/api";

import { useUpdateDatasetMutation } from "./dataset.slice";
import EditCollectionOrFieldForm, {
  FORM_ID,
} from "./EditCollectionOrFieldForm";
import {
  getUpdatedDatasetFromCollection,
  removeCollectionFromDataset,
} from "./helpers";

const DESCRIPTION =
  "Collections are an array of objects that describe the Dataset's collections. Provide additional context to this collection by filling out the fields below.";
interface Props {
  dataset: Dataset;
  collection: DatasetCollection;
  isOpen: boolean;
  onClose: () => void;
}
const EditCollectionDrawer = ({
  dataset,
  collection,
  isOpen,
  onClose,
}: Props) => {
  const collectionIndex = useMemo(
    () => dataset?.collections.indexOf(collection),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );
  const [updateDataset] = useUpdateDatasetMutation();
  const toast = useToast();
  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  const handleSubmit = async (
    values: Pick<DatasetCollection, "description" | "data_categories">,
  ) => {
    const updatedCollection = { ...collection, ...values };
    const updatedDataset = getUpdatedDatasetFromCollection(
      dataset!,
      updatedCollection,
      collectionIndex!,
    );
    try {
      await updateDataset(updatedDataset);
      toast(successToastParams("Successfully modified collection"));
    } catch (error) {
      toast(errorToastParams(error as string));
    }
    onClose();
  };

  const handleDelete = async () => {
    if (dataset && collectionIndex !== undefined) {
      const updatedDataset = removeCollectionFromDataset(
        dataset,
        collectionIndex,
      );
      try {
        await updateDataset(updatedDataset);
        toast(successToastParams("Successfully deleted collection"));
      } catch (error) {
        toast(errorToastParams(error as string));
      }
      onClose();
      onDeleteClose();
    }
  };

  return (
    <>
      <EditDrawer
        isOpen={isOpen}
        onClose={onClose}
        description={DESCRIPTION}
        header={
          <EditDrawerHeader title={`Collection Name: ${collection?.name}`} />
        }
        footer={
          <EditDrawerFooter
            onClose={onClose}
            onDelete={onDeleteOpen}
            formId={FORM_ID}
          />
        }
      >
        <EditCollectionOrFieldForm
          values={collection}
          onSubmit={handleSubmit}
          dataType="collection"
          showDataCategories={false}
        />
      </EditDrawer>
      <ConfirmationModal
        isOpen={deleteIsOpen}
        onClose={onDeleteClose}
        onConfirm={handleDelete}
        title="Delete Collection"
        message={
          <Text>
            You are about to permanently delete the collection named{" "}
            <Text color="complimentary.500" as="span" fontWeight="bold">
              {collection?.name}
            </Text>{" "}
            from this dataset. Are you sure you would like to continue?
          </Text>
        }
      />
    </>
  );
};

export default EditCollectionDrawer;
