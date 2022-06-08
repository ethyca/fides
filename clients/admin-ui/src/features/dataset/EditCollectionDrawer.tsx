import { useSelector } from "react-redux";

import {
  selectActiveCollectionIndex,
  selectActiveDataset,
  useUpdateDatasetMutation,
} from "./dataset.slice";
import EditCollectionOrFieldForm from "./EditCollectionOrFieldForm";
import EditDrawer from "./EditDrawer";
import { getUpdatedDatasetFromCollection } from "./helpers";
import { DatasetCollection } from "./types";

const DESCRIPTION =
  "By providing a small amount of additional context for each system we can make reporting and understanding our tech stack much easier.";
interface Props {
  collection: DatasetCollection;
  isOpen: boolean;
  onClose: () => void;
}
const EditCollectionDrawer = ({ collection, isOpen, onClose }: Props) => {
  const dataset = useSelector(selectActiveDataset);
  const collectionIndex = useSelector(selectActiveCollectionIndex);
  const [updateDataset] = useUpdateDatasetMutation();

  const handleSubmit = (
    values: Pick<
      DatasetCollection,
      "description" | "data_qualifier" | "data_categories"
    >
  ) => {
    if (dataset && collectionIndex != null) {
      const updatedCollection = { ...collection, ...values };
      const updatedDataset = getUpdatedDatasetFromCollection(
        dataset,
        updatedCollection,
        collectionIndex
      );
      updateDataset(updatedDataset);
      onClose();
    }
  };

  return (
    <EditDrawer
      isOpen={isOpen}
      onClose={onClose}
      description={DESCRIPTION}
      header={`Collection name: ${collection.name}`}
    >
      <EditCollectionOrFieldForm
        values={collection}
        onClose={onClose}
        onSubmit={handleSubmit}
      />
      {/* <EditFieldForm field={field} onClose={onClose} /> */}
    </EditDrawer>
  );
};

export default EditCollectionDrawer;
