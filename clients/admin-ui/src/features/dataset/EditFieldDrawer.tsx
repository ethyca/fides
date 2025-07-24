import { ConfirmationModal, Text, useDisclosure } from "fidesui";
import { cloneDeep, set, update } from "lodash";

import EditDrawer, {
  EditDrawerFooter,
  EditDrawerHeader,
} from "~/features/common/EditDrawer";
import { Dataset, DatasetField } from "~/types/api";

import { useUpdateDatasetMutation } from "./dataset.slice";
import EditCollectionOrFieldForm, {
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

const EditFieldDrawer = ({
  field,
  isOpen,
  onClose,
  dataset,
  collectionName,
  subfields,
}: Props) => {
  const [updateDataset] = useUpdateDatasetMutation();
  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  const handleSubmit = (
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

    updateDataset(updatedDataset);
    onClose();
  };

  const handleDelete = () => {
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

    updateDataset(updatedDataset);
    onClose();
    onDeleteClose();
  };

  return (
    <>
      <EditDrawer
        isOpen={isOpen}
        onClose={onClose}
        description={DESCRIPTION}
        header={<EditDrawerHeader title={`Field Name: ${field?.name}`} />}
        footer={
          <EditDrawerFooter
            onClose={onClose}
            onDelete={onDeleteOpen}
            formId={FORM_ID}
          />
        }
      >
        <EditCollectionOrFieldForm
          values={field!}
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
              {field?.name}
            </Text>{" "}
            from this dataset. Are you sure you would like to continue?
          </Text>
        }
      />
    </>
  );
};

export default EditFieldDrawer;
