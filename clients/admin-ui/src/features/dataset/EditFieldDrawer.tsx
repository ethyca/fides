import { Text } from "@fidesui/react";
import { useSelector } from "react-redux";

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
import EditDrawer from "./EditDrawer";
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

  const handleSubmit = (
    values: Pick<
      DatasetField,
      "description" | "data_qualifier" | "data_categories"
    >
  ) => {
    // merge the updated fields with the original dataset
    if (dataset && collectionIndex !== undefined && fieldIndex !== undefined) {
      const updatedField = { ...field, ...values };
      const updatedDataset = getUpdatedDatasetFromField(
        dataset,
        updatedField,
        collectionIndex,
        fieldIndex
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
        fieldIndex
      );
      updateDataset(updatedDataset);
      onClose();
    }
  };

  return (
    <EditDrawer
      isOpen={isOpen}
      onClose={onClose}
      header={`Field Name: ${field.name}`}
      description={DESCRIPTION}
      onDelete={handleDelete}
      deleteTitle="Delete Field"
      deleteMessage={
        <Text>
          You are about to permanently delete the field named{" "}
          <Text color="complimentary.500" as="span" fontWeight="bold">
            {field.name}
          </Text>{" "}
          from this dataset. Are you sure you would like to continue?
        </Text>
      }
      formId={FORM_ID}
    >
      <EditCollectionOrFieldForm
        values={field}
        onSubmit={handleSubmit}
        dataType="field"
      />
    </EditDrawer>
  );
};

export default EditFieldDrawer;
