import { useSelector } from "react-redux";

import {
  selectActiveCollectionIndex,
  selectActiveDataset,
  selectActiveFieldIndex,
  useUpdateDatasetMutation,
} from "./dataset.slice";
import EditCollectionOrFieldForm from "./EditCollectionOrFieldForm";
import EditDrawer from "./EditDrawer";
import { getUpdatedDatasetFromField } from "./helpers";
import { DatasetField } from "./types";

interface Props {
  field: DatasetField;
  isOpen: boolean;
  onClose: () => void;
}

const DESCRIPTION =
  "By providing a small amount of additional context for each system we can make reporting and understanding our tech stack much easier.";

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
    if (dataset && collectionIndex != null && fieldIndex != null) {
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

  return (
    <EditDrawer
      isOpen={isOpen}
      onClose={onClose}
      header={`Field Name: ${field.name}`}
      description={DESCRIPTION}
    >
      <EditCollectionOrFieldForm
        values={field}
        onClose={onClose}
        onSubmit={handleSubmit}
      />
    </EditDrawer>
  );
};

export default EditFieldDrawer;
