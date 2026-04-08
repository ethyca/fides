import { Text, useMessage, useModal } from "fidesui";
import { cloneDeep, set, update } from "lodash";

import EditDrawer, {
  EditDrawerFooter,
  EditDrawerHeader,
} from "~/features/common/EditDrawer";
import { Dataset, DatasetField } from "~/types/api";

import { useUpdateDatasetMutation } from "./dataset.slice";
import {
  EditCollectionOrFieldForm,
  FORM_ID,
} from "./EditCollectionOrFieldForm";
import { getDatasetPath } from "./helpers";

interface Props {
  isOpen: boolean;
  onClose: () => void;

  dataset: Dataset;
  collectionName: string;
  field?: DatasetField;
  subfields?: string[];
}

const DESCRIPTION =
  "Fields are an array of objects that describe the collection's fields. Provide additional context to this field by filling out the fields below.";

export const EditFieldDrawer = ({
  field,
  isOpen,
  onClose,
  dataset,
  collectionName,
  subfields,
}: Props) => {
  const [updateDataset] = useUpdateDatasetMutation();
  const message = useMessage();
  const confirmModal = useModal();

  const handleSubmit = async (
    values: Pick<DatasetField, "description" | "data_categories">,
  ) => {
    const pathToField = getDatasetPath({
      dataset: dataset!,
      collectionName,
      subfields: subfields
        ? [...subfields, field?.name || ""]
        : [field?.name || ""],
    });

    const updatedField = { ...field!, ...values };
    const updatedDataset = cloneDeep(dataset!);
    set(updatedDataset, pathToField, updatedField);

    try {
      await updateDataset(updatedDataset);
      message.success("Successfully modified field");
    } catch (error) {
      message.error(error as string);
    }
    onClose();
  };

  const handleDelete = async () => {
    const pathToParentField = getDatasetPath({
      dataset: dataset!,
      collectionName,
      subfields,
    });

    const updatedDataset = cloneDeep(dataset!);
    update(updatedDataset, pathToParentField, (parentField) => ({
      ...parentField,
      fields: parentField.fields.filter(
        (f: DatasetField) => f.name !== field?.name,
      ),
    }));

    try {
      await updateDataset(updatedDataset);
      message.success("Successfully deleted field");
    } catch (error) {
      message.error(error as string);
    }
    onClose();
  };

  const confirmDelete = () => {
    confirmModal.confirm({
      title: "Delete Field",
      content: (
        <>
          You are about to permanently delete the field named{" "}
          <Text strong>{field?.name}</Text> from this dataset. Are you sure you
          would like to continue?
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
      header={<EditDrawerHeader title={`Field Name: ${field?.name}`} />}
      footer={<EditDrawerFooter onDelete={confirmDelete} formId={FORM_ID} />}
    >
      {field && (
        <EditCollectionOrFieldForm
          values={field}
          onSubmit={handleSubmit}
          dataType="field"
        />
      )}
    </EditDrawer>
  );
};
