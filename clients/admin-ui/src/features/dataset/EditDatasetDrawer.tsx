import { useToast } from "@fidesui/react";

import { errorToastParams, successToastParams } from "../common/toast";
import { useUpdateDatasetMutation } from "./dataset.slice";
import EditDatasetForm from "./EditDatasetForm";
import EditDrawer from "./EditDrawer";
import { Dataset } from "./types";

const DESCRIPTION =
  "A Dataset takes a database schema (tables and columns) and adds Fides privacy categorizations. Provide additional context to this dataset by filling out the fields below.";
interface Props {
  dataset: Dataset;
  isOpen: boolean;
  onClose: () => void;
}
const EditDatasetDrawer = ({ dataset, isOpen, onClose }: Props) => {
  const [updateDataset] = useUpdateDatasetMutation();
  const toast = useToast();

  const handleSubmit = async (values: Partial<Dataset>) => {
    if (dataset) {
      const updatedDataset = { ...dataset, ...values };
      try {
        const result = await updateDataset(updatedDataset);
        // TODO: we should systematically coerce errors into their types (see fidesops)
        if ("error" in result && "data" in result.error) {
          if ("data" in result.error) {
            toast(errorToastParams(result.error.data as string));
          } else {
            toast(errorToastParams("An unknown error occurred"));
          }
        } else {
          toast(successToastParams("Successfully modified dataset"));
        }
      } catch (error) {
        toast(errorToastParams(error as string));
      }
      onClose();
    }
  };

  return (
    <EditDrawer
      isOpen={isOpen}
      onClose={onClose}
      description={DESCRIPTION}
      header={`Dataset Name: ${dataset.name}`}
      onDelete={() => {}} // TODO #769
    >
      <EditDatasetForm
        values={dataset}
        onClose={onClose}
        onSubmit={handleSubmit}
      />
    </EditDrawer>
  );
};

export default EditDatasetDrawer;
