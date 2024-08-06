import { errorToastParams, successToastParams } from "common/toast";
import { ConfirmationModal, Text, useDisclosure, useToast } from "fidesui";
import { useSelector } from "react-redux";

import EditDrawer, {
  EditDrawerFooter,
  EditDrawerHeader,
} from "~/features/common/EditDrawer";
import { DatasetCollection } from "~/types/api";

import {
  selectActiveCollectionIndex,
  selectActiveDataset,
  setActiveCollectionIndex,
  useUpdateDatasetMutation,
} from "./dataset.slice";
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
  collection: DatasetCollection;
  isOpen: boolean;
  onClose: () => void;
}
const EditCollectionDrawer = ({ collection, isOpen, onClose }: Props) => {
  const dataset = useSelector(selectActiveDataset);
  const collectionIndex = useSelector(selectActiveCollectionIndex);
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
    if (dataset && collectionIndex !== undefined) {
      const updatedCollection = { ...collection, ...values };
      const updatedDataset = getUpdatedDatasetFromCollection(
        dataset,
        updatedCollection,
        collectionIndex,
      );
      try {
        await updateDataset(updatedDataset);
        toast(successToastParams("Successfully modified collection"));
      } catch (error) {
        toast(errorToastParams(error as string));
      }
      onClose();
    }
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
        const newActiveCollectionIndex =
          dataset.collections.length > 0 ? 0 : undefined;
        setActiveCollectionIndex(newActiveCollectionIndex);
      } catch (error) {
        toast(errorToastParams(error as string));
      }
      onClose();
    }
  };

  return (
    <>
      <EditDrawer
        isOpen={isOpen}
        onClose={onClose}
        description={DESCRIPTION}
        header={
          <EditDrawerHeader
            title={`Collection Name: ${collection.name}`}
            onDelete={onDeleteOpen}
          />
        }
        footer={<EditDrawerFooter onClose={onClose} formId={FORM_ID} />}
      >
        <EditCollectionOrFieldForm
          values={collection}
          onSubmit={handleSubmit}
          dataType="collection"
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
              {collection.name}
            </Text>{" "}
            from this dataset. Are you sure you would like to continue?
          </Text>
        }
      />
    </>
  );
};

export default EditCollectionDrawer;
