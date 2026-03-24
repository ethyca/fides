import {
  ChakraText as Text,
  ConfirmationModal,
  useChakraDisclosure as useDisclosure,
  useMessage,
} from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

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
import EditDatasetForm, { FORM_ID } from "./EditDatasetForm";

const DESCRIPTION =
  "A Dataset takes a database schema (tables and columns) and adds Fides privacy categorizations. Provide additional context to this dataset by filling out the fields below.";
interface Props {
  dataset?: Dataset;
  isOpen: boolean;
  onClose: () => void;
}
const EditDatasetDrawer = ({ dataset, isOpen, onClose }: Props) => {
  const [updateDataset, { isLoading }] = useUpdateDatasetMutation();
  const [deleteDataset] = useDeleteDatasetMutation();
  const router = useRouter();
  const message = useMessage();
  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();
  const {
    isOpen: yamlIsOpen,
    onOpen: onYamlOpen,
    onClose: onYamlClose,
  } = useDisclosure();

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
    setActiveDatasetFidesKey(undefined);
    router.push("/dataset");
    onClose();
    onDeleteClose();
  };

  return (
    <>
      <EditDrawer
        isOpen={isOpen}
        onClose={onClose}
        description={DESCRIPTION}
        header={<EditDrawerHeader title={`Edit: ${dataset?.name}`} />}
        footer={
          <EditDrawerFooter
            onDelete={onDeleteOpen}
            onEditYaml={() => onYamlOpen()}
            formId={FORM_ID}
          />
        }
      >
        <YamlEditorModal
          isOpen={yamlIsOpen}
          onClose={onYamlClose}
          onChange={setDatasetYaml}
          onSubmit={() => handleSubmit(datasetYaml!)}
          title="Edit dataset YAML"
          isLoading={isLoading}
          isDatasetSelected={false}
          dataset={dataset}
        />
        {dataset && (
          <EditDatasetForm values={dataset} onSubmit={handleSubmit} />
        )}
      </EditDrawer>
      <ConfirmationModal
        isOpen={deleteIsOpen}
        onClose={onDeleteClose}
        onConfirm={handleDelete}
        title="Delete Dataset"
        message={
          <Text>
            You are about to permanently delete the dataset named{" "}
            <Text color="complimentary.500" as="span" fontWeight="bold">
              {dataset?.name}
            </Text>
            . Are you sure you would like to continue?
          </Text>
        }
      />
    </>
  );
};

export default EditDatasetDrawer;
