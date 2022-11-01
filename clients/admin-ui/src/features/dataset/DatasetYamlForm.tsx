import { useToast } from "@fidesui/react";
import { useRouter } from "next/router";

import { Dataset } from "~/types/api";

import { successToastParams } from "../common/toast";
import YamlForm from "../YamlForm";
import {
  setActiveDatasetFidesKey,
  useCreateDatasetMutation,
} from "./dataset.slice";

// handle the common case where everything is nested under a `dataset` key
interface NestedDataset {
  dataset: Dataset[];
}
export function isDatasetArray(value: unknown): value is NestedDataset {
  return (
    typeof value === "object" &&
    value != null &&
    "dataset" in value &&
    Array.isArray((value as any).dataset)
  );
}

const DESCRIPTION =
  "Get started creating your first dataset by pasting your dataset yaml below! You may have received this yaml from a colleague or your Ethyca developer support engineer.";

const DatasetYamlForm = () => {
  const [createDataset] = useCreateDatasetMutation();
  const toast = useToast();
  const router = useRouter();

  const handleCreate = async (yaml: unknown) => {
    let dataset;
    if (isDatasetArray(yaml)) {
      [dataset] = yaml.dataset;
    } else {
      dataset = yaml;
    }

    return createDataset(dataset);
  };

  const handleSuccess = (newDataset: Dataset) => {
    toast(successToastParams("Successfully loaded new dataset YAML"));
    setActiveDatasetFidesKey(newDataset.fides_key);
    router.push(`/dataset/${newDataset.fides_key}`);
  };

  return (
    <YamlForm<Dataset>
      description={DESCRIPTION}
      submitButtonText="Create dataset"
      onCreate={handleCreate}
      onSuccess={handleSuccess}
    />
  );
};

export default DatasetYamlForm;
