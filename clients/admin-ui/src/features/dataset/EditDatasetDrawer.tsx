import { Text, useMessage, useModal } from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";
import { useDispatch } from "react-redux";

import EditDrawer, {
  EditDrawerFooter,
  EditDrawerHeader,
} from "~/features/common/EditDrawer";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import YamlEditorModal from "~/features/datastore-connections/system_portal_config/forms/fields/DatasetConfigField/YamlEditorModal";
import { Dataset } from "~/types/api";

import {
  setActiveDatasetFidesKey,
  useDeleteDatasetMutation,
  useUpdateDatasetMutation,
} from "./dataset.slice";
import { EditDatasetForm, FORM_ID } from "./EditDatasetForm";

const DESCRIPTION =
  "A Dataset takes a database schema (tables and columns) and adds Fides privacy categorizations. Provide additional context to this dataset by filling out the fields below.";

interface Props {
  dataset?: Dataset;
  isOpen: boolean;
  onClose: () => void;
}

export const EditDatasetDrawer = ({ dataset, isOpen, onClose }: Props) => {
  const [updateDataset, { isLoading }] = useUpdateDatasetMutation();
  const [deleteDataset] = useDeleteDatasetMutation();
  const router = useRouter();
  const dispatch = useDispatch();
  const message = useMessage();
  const confirmModal = useModal();
  const [yamlOpen, setYamlOpen] = useState(false);

  const [datasetYaml, setDatasetYaml] = useState<Dataset | undefined>(
    undefined,
  );

  const handleSubmit = async (values: Partial<Dataset>) => {
    const updatedDataset = { ...dataset!, ...values };
    try {
      const result = await updateDataset(updatedDataset);
      if (isErrorResult(result)) {
        message.error(getErrorMessage(result.error));
      } else {
        message.success("Successfully modified dataset");
      }
    } catch (error) {
      message.error(error as string);
    }
    onClose();
  };

  const handleDelete = async () => {
    const { fides_key: fidesKey } = dataset!;
    const result = await deleteDataset(fidesKey);

    if (isErrorResult(result)) {
      message.error(getErrorMessage(result.error));
    } else {
      message.success("Successfully deleted dataset");
    }
    dispatch(setActiveDatasetFidesKey(undefined));
    router.push("/dataset");
    onClose();
  };

  const confirmDelete = () => {
    confirmModal.confirm({
      title: "Delete Dataset",
      content: (
        <>
          You are about to permanently delete the dataset named{" "}
          <Text strong>{dataset?.name}</Text>. Are you sure you would like to
          continue?
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
      header={<EditDrawerHeader title={`Edit: ${dataset?.name}`} />}
      footer={
        <EditDrawerFooter
          onDelete={confirmDelete}
          onEditYaml={() => setYamlOpen(true)}
          formId={FORM_ID}
        />
      }
    >
      <YamlEditorModal
        isOpen={yamlOpen}
        onClose={() => setYamlOpen(false)}
        onChange={setDatasetYaml}
        onSubmit={() => handleSubmit(datasetYaml!)}
        title="Edit dataset YAML"
        isLoading={isLoading}
        isDatasetSelected={false}
        dataset={dataset}
      />
      {dataset && <EditDatasetForm values={dataset} onSubmit={handleSubmit} />}
    </EditDrawer>
  );
};
