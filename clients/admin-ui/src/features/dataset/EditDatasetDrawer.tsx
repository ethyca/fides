import { Text, useToast } from "@fidesui/react";
import { useRouter } from "next/router";

import { errorToastParams, successToastParams } from "../common/toast";
import {
  setActiveDataset,
  useDeleteDatasetMutation,
  useUpdateDatasetMutation,
} from "./dataset.slice";
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
  const [deleteDataset] = useDeleteDatasetMutation();
  const router = useRouter();
  const toast = useToast();

  const handleSubmit = async (values: Partial<Dataset>) => {
    const updatedDataset = { ...dataset, ...values };
    try {
      const result = await updateDataset(updatedDataset);
      // TODO: we should systematically coerce errors into their types (#803)
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
  };

  const handleDelete = async () => {
    const { fides_key: fidesKey } = dataset;
    const result = await deleteDataset(fidesKey);
    // TODO: we should systematically coerce errors into their types (#803)
    if ("error" in result && "data" in result.error) {
      if ("data" in result.error) {
        toast(errorToastParams(result.error.data as string));
      } else {
        toast(errorToastParams("An unknown error occurred"));
      }
    } else {
      toast(successToastParams("Successfully deleted dataset"));
    }
    setActiveDataset(null);
    router.push("/dataset");
    onClose();
  };

  return (
    <EditDrawer
      isOpen={isOpen}
      onClose={onClose}
      description={DESCRIPTION}
      header={`Dataset Name: ${dataset.name}`}
      onDelete={handleDelete}
      deleteMessage={
        <Text>
          You are about to permanently delete the dataset named{" "}
          <Text color="complimentary.500" as="span" fontWeight="bold">
            {dataset.name}
          </Text>
          . Are you sure you would like to continue?
        </Text>
      }
      deleteTitle="Delete Dataset"
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
