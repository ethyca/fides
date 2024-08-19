import { ConfirmationModal, Text, useDisclosure } from "fidesui";

import EditDrawer, {
  EditDrawerFooter,
  EditDrawerHeader,
} from "~/features/common/EditDrawer";
import { Dataset, DatasetCollection, DatasetField } from "~/types/api";

import { useUpdateDatasetMutation } from "./dataset.slice";
import EditCollectionOrFieldForm, {
  FORM_ID,
} from "./EditCollectionOrFieldForm";
import { getUpdatedDatasetFromField, removeFieldFromDataset } from "./helpers";

interface Props {
  isOpen: boolean;
  onClose: () => void;

  dataset: Dataset;
  collection: DatasetCollection;
  field?: DatasetField;
}

const DESCRIPTION =
  "Fields are an array of objects that describe the collection's fields. Provide additional context to this field by filling out the fields below.";

const EditFieldDrawer = ({
  field,
  isOpen,
  onClose,
  dataset,
  collection,
}: Props) => {
  const [updateDataset] = useUpdateDatasetMutation();
  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  const handleSubmit = (
    values: Pick<DatasetField, "description" | "data_categories">,
  ) => {
    // merge the updated fields with the original dataset
    const updatedField = { ...field!, ...values };
    const collectionIndex = dataset.collections.indexOf(collection);
    const fieldIndex = collection.fields.indexOf(field!);
    const updatedDataset = getUpdatedDatasetFromField(
      dataset,
      updatedField,
      collectionIndex,
      fieldIndex,
    );
    updateDataset(updatedDataset);
    onClose();
  };

  const handleDelete = () => {
    const collectionIndex = dataset.collections.indexOf(collection);
    const fieldIndex = collection.fields.indexOf(field!);

    const updatedDataset = removeFieldFromDataset(
      dataset,
      collectionIndex,
      fieldIndex,
    );
    updateDataset(updatedDataset);
    onClose();
    onDeleteClose();
  };

  return (
    <>
      <EditDrawer
        isOpen={isOpen}
        onClose={onClose}
        description={DESCRIPTION}
        header={<EditDrawerHeader title={`Field Name: ${field?.name}`} />}
        footer={
          <EditDrawerFooter
            onClose={onClose}
            onDelete={onDeleteOpen}
            formId={FORM_ID}
          />
        }
      >
        <EditCollectionOrFieldForm
          values={field!}
          onSubmit={handleSubmit}
          dataType="field"
        />
      </EditDrawer>
      <ConfirmationModal
        isOpen={deleteIsOpen}
        onClose={onDeleteClose}
        onConfirm={handleDelete}
        title="Delete Field"
        message={
          <Text>
            You are about to permanently delete the field named{" "}
            <Text color="complimentary.500" as="span" fontWeight="bold">
              {field?.name}
            </Text>{" "}
            from this dataset. Are you sure you would like to continue?
          </Text>
        }
      />
    </>
  );
};

export default EditFieldDrawer;
