import { Text, useMessage, useModal } from "fidesui";
import { useMemo } from "react";

import EditDrawer, {
  EditDrawerFooter,
  EditDrawerHeader,
} from "~/features/common/EditDrawer";
import { Dataset, DatasetCollection } from "~/types/api";

import { useUpdateDatasetMutation } from "./dataset.slice";
import {
  EditCollectionOrFieldForm,
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

export const EditCollectionDrawer = ({
  dataset,
  collection,
  isOpen,
  onClose,
}: Props) => {
  const collectionIndex = useMemo(
    () => dataset?.collections.indexOf(collection),
    [collection, dataset?.collections],
  );
  const [updateDataset] = useUpdateDatasetMutation();
  const message = useMessage();
  const confirmModal = useModal();

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
      message.success("Successfully modified collection");
    } catch (error) {
      message.error(error as string);
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
        message.success("Successfully deleted collection");
      } catch (error) {
        message.error(error as string);
      }
      onClose();
    }
  };

  const confirmDelete = () => {
    confirmModal.confirm({
      title: "Delete Collection",
      content: (
        <>
          You are about to permanently delete the collection named{" "}
          <Text strong>{collection?.name}</Text> from this dataset. Are you sure
          you would like to continue?
        </>
      ),
      okButtonProps: { danger: true },
      onOk: handleDelete,
    });
  };

  return (
    <EditDrawer
      isOpen={isOpen}
      onClose={onClose}
      description={DESCRIPTION}
      header={
        <EditDrawerHeader title={`Collection Name: ${collection?.name}`} />
      }
      footer={<EditDrawerFooter onDelete={confirmDelete} formId={FORM_ID} />}
    >
      <EditCollectionOrFieldForm
        values={collection}
        onSubmit={handleSubmit}
        dataType="collection"
        showDataCategories={false}
      />
    </EditDrawer>
  );
};
