import { ConfirmationModal, Text, useDisclosure } from "fidesui";
import { useSelector } from "react-redux";

import EditDrawer, {
  EditDrawerFooter,
  EditDrawerHeader,
} from "~/features/common/EditDrawer";
import { DatasetField } from "~/types/api";

import {
  selectActiveCollectionIndex,
  selectActiveDataset,
  selectActiveFieldIndex,
  useUpdateDatasetMutation,
} from "./dataset.slice";
import EditCollectionOrFieldForm, {
  FORM_ID,
} from "./EditCollectionOrFieldForm";
import { getUpdatedDatasetFromField, removeFieldFromDataset } from "./helpers";

interface Props {
  field: DatasetField;
  isOpen: boolean;
  onClose: () => void;
}

const DESCRIPTION =
  "Fields are an array of objects that describe the collection's fields. Provide additional context to this field by filling out the fields below.";

const EditFieldDrawer = ({ field, isOpen, onClose }: Props) => {
  const dataset = useSelector(selectActiveDataset);
  const collectionIndex = useSelector(selectActiveCollectionIndex);
  const fieldIndex = useSelector(selectActiveFieldIndex);
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
    if (dataset && collectionIndex !== undefined && fieldIndex !== undefined) {
      const updatedField = { ...field, ...values };
      const updatedDataset = getUpdatedDatasetFromField(
        dataset,
        updatedField,
        collectionIndex,
        fieldIndex,
      );
      updateDataset(updatedDataset);
      onClose();
    }
  };

  const handleDelete = () => {
    if (dataset && collectionIndex !== undefined && fieldIndex !== undefined) {
      const updatedDataset = removeFieldFromDataset(
        dataset,
        collectionIndex,
        fieldIndex,
      );
      updateDataset(updatedDataset);
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
            title={`Field Name: ${field.name}`}
            onDelete={onDeleteOpen}
          />
        }
        footer={<EditDrawerFooter onClose={onClose} formId={FORM_ID} />}
      >
        <EditCollectionOrFieldForm
          values={field}
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
              {field.name}
            </Text>{" "}
            from this dataset. Are you sure you would like to continue?
          </Text>
        }
      />
    </>
  );
};

export default EditFieldDrawer;
