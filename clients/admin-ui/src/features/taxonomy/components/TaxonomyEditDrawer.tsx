import {
  AntForm,
  ConfirmationModal,
  Stack,
  Text,
  useDisclosure,
  useToast,
} from "fidesui";

import { useCustomFields } from "~/features/common/custom-fields";
import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { isErrorResult } from "~/types/errors";

import EditDrawer, {
  EditDrawerFooter,
  EditDrawerHeader,
} from "../../common/EditDrawer";
import { taxonomyTypeToResourceType } from "../helpers";
import useTaxonomySlices from "../hooks/useTaxonomySlices";
import { TaxonomyEntity } from "../types";
import { CoreTaxonomiesEnum } from "../types/CoreTaxonomiesEnum";
import TaxonomyCustomFieldsForm from "./TaxonomyCustomFieldsForm";
import TaxonomyEditForm from "./TaxonomyEditForm";

interface TaxonomyEditDrawerProps {
  taxonomyItem?: TaxonomyEntity | null;
  taxonomyType: CoreTaxonomiesEnum;
  onClose: () => void;
}

const TaxonomyEditDrawer = ({
  taxonomyItem,
  taxonomyType,
  onClose: closeDrawer,
}: TaxonomyEditDrawerProps) => {
  // Using separate forms for taxonomies & their custom fields
  // because custom fields are not part of the taxonomy and
  // uses dedicated endpoints
  const TAXONOMY_FORM_ID = "edit-taxonomy-form";
  const [taxonomyForm] = AntForm.useForm();

  const CUSTOM_FIELDS_FORM_ID = "custom-fields-form";
  const [customFieldsForm] = AntForm.useForm();

  const isCustomTaxonomy = !taxonomyItem?.is_default;

  const toast = useToast();

  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  const { updateTrigger, deleteTrigger } = useTaxonomySlices({ taxonomyType });

  const customFields = useCustomFields({
    resourceFidesKey: taxonomyItem?.fides_key,
    resourceType: taxonomyTypeToResourceType(taxonomyType)!,
  });

  const handleEdit = async (formValues: TaxonomyEntity) => {
    const result = await updateTrigger(formValues);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }

    if (customFields.isEnabled) {
      const customFieldValues = customFieldsForm.getFieldsValue();
      await customFields.upsertCustomFields({
        fides_key: taxonomyItem?.fides_key!,
        customFieldValues,
      });
    }

    toast(successToastParams("Taxonomy successfully updated"));
    closeDrawer();
  };

  const handleDelete = async () => {
    await deleteTrigger(taxonomyItem!.fides_key);
    onDeleteClose();
    closeDrawer();
  };

  if (customFields.isEnabled && customFields.isLoading) {
    return null;
  }

  return (
    <>
      <EditDrawer
        isOpen={!!taxonomyItem}
        onClose={closeDrawer}
        header={<EditDrawerHeader title={taxonomyItem?.name || ""} />}
        footer={
          <EditDrawerFooter
            onClose={closeDrawer}
            onDelete={isCustomTaxonomy ? onDeleteOpen : undefined}
            formId={TAXONOMY_FORM_ID}
          />
        }
      >
        <div className="mb-4">
          <h3 className="mb-3 font-semibold text-gray-700">Details</h3>
          <div className="flex">
            <span className="w-1/3 text-sm text-gray-500">Fides key:</span>
            <span>{taxonomyItem?.fides_key}</span>
          </div>
          {/* <div className="flex">
            <span className=" w-1/3 text-sm text-gray-500">Qualifiers:</span>
            <span />
          </div> */}
        </div>
        {taxonomyItem && (
          <TaxonomyEditForm
            initialValues={taxonomyItem}
            onSubmit={handleEdit}
            form={taxonomyForm}
            formId={TAXONOMY_FORM_ID}
            taxonomyType={taxonomyType}
          />
        )}
        {customFields.isEnabled && (
          <TaxonomyCustomFieldsForm
            form={customFieldsForm}
            formId={CUSTOM_FIELDS_FORM_ID}
            customFields={customFields}
          />
        )}
      </EditDrawer>

      <ConfirmationModal
        isOpen={deleteIsOpen}
        onClose={onDeleteClose}
        onConfirm={handleDelete}
        title={`Delete ${taxonomyType}`}
        message={
          <Stack>
            <Text>
              You are about to permanently delete the {taxonomyType}{" "}
              <Text color="complimentary.500" as="span" fontWeight="bold">
                {taxonomyItem?.name}
              </Text>{" "}
              from your taxonomy. Are you sure you would like to continue?
            </Text>
          </Stack>
        }
      />
    </>
  );
};
export default TaxonomyEditDrawer;
