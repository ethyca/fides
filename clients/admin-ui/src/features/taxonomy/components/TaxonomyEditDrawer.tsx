import {
  AntButton as Button,
  AntForm as Form,
  AntTooltip as Tooltip,
  AntTypography as Typography,
  ConfirmationModal,
  DrawerFooter,
  EyeIcon,
  Stack,
  Text,
  useDisclosure,
  useToast,
} from "fidesui";

import { useCustomFields } from "~/features/common/custom-fields";
import { getErrorMessage } from "~/features/common/helpers";
import { TrashCanOutlineIcon } from "~/features/common/Icon/TrashCanOutlineIcon";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { isErrorResult } from "~/types/errors";

import EditDrawer, { EditDrawerHeader } from "../../common/EditDrawer";
import { CoreTaxonomiesEnum } from "../constants";
import { taxonomyTypeToResourceType } from "../helpers";
import useTaxonomySlices from "../hooks/useTaxonomySlices";
import { TaxonomyEntity } from "../types";
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
  const [taxonomyForm] = Form.useForm();

  const CUSTOM_FIELDS_FORM_ID = "custom-fields-form";
  const [customFieldsForm] = Form.useForm();

  const toast = useToast();

  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  const { updateTrigger } = useTaxonomySlices({ taxonomyType });

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
    // For record keeping, we will not actually delete the taxonomy
    // but rather mark it as disabled and not show it in the UI
    await updateTrigger({
      ...taxonomyItem!,
      active: false,
    });
    onDeleteClose();
    closeDrawer();
  };

  const handleEnable = async () => {
    await updateTrigger({
      ...taxonomyItem!,
      active: true,
    });
    onDeleteClose();
    closeDrawer();
  };

  return (
    <>
      <EditDrawer
        isOpen={!!taxonomyItem}
        onClose={closeDrawer}
        header={<EditDrawerHeader title={taxonomyItem?.name || ""} />}
        footer={
          <DrawerFooter justifyContent="space-between">
            {taxonomyItem?.active ? (
              <Button
                aria-label="delete"
                icon={<TrashCanOutlineIcon fontSize="small" />}
                onClick={onDeleteOpen}
                data-testid="delete-btn"
              />
            ) : (
              <Tooltip title="Enable label">
                <Button
                  aria-label="enable"
                  onClick={handleEnable}
                  data-testid="enable-btn"
                  icon={<EyeIcon fontSize="small" />}
                />
              </Tooltip>
            )}

            <div className="flex gap-2">
              <Button
                htmlType="submit"
                type="primary"
                data-testid="save-btn"
                form={TAXONOMY_FORM_ID}
              >
                Save
              </Button>
            </div>
          </DrawerFooter>
        }
      >
        <div className="mb-4">
          <Typography.Title level={5}>Details</Typography.Title>
          <div className="flex">
            <span className="w-1/3 shrink-0 text-sm text-gray-500">
              Fides key:
            </span>
            <Tooltip title={taxonomyItem?.fides_key} trigger="click">
              <span
                className="flex-1 truncate"
                data-testid="edit-drawer-fides-key"
              >
                {taxonomyItem?.fides_key}
              </span>
            </Tooltip>
          </div>
        </div>
        {!!taxonomyItem && (
          <TaxonomyEditForm
            initialValues={taxonomyItem}
            onSubmit={handleEdit}
            form={taxonomyForm}
            formId={TAXONOMY_FORM_ID}
            taxonomyType={taxonomyType}
          />
        )}
        {customFields.isEnabled && !customFields.isLoading && (
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
