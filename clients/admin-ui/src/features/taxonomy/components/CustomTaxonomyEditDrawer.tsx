import { AntButton as Button, AntFlex as Flex, useMessage } from "fidesui";

import { useCustomFields } from "~/features/common/custom-fields";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { DetailsDrawer } from "~/features/data-discovery-and-detection/action-center/fields/DetailsDrawer";
import { DetailsDrawerProps } from "~/features/data-discovery-and-detection/action-center/fields/DetailsDrawer/types";
import CustomTaxonomyDetails from "~/features/taxonomy/components/CustomTaxonomyDetails";
import { useUpdateCustomTaxonomyMutation } from "~/features/taxonomy/taxonomy.slice";
import { CustomFieldDefinitionWithId } from "~/types/api";
import { TaxonomyResponse } from "~/types/api/models/TaxonomyResponse";
import { TaxonomyUpdate } from "~/types/api/models/TaxonomyUpdate";

interface CustomTaxonomyEditDrawerProps
  extends Omit<DetailsDrawerProps, "itemKey"> {
  taxonomy: TaxonomyResponse;
  onDelete: () => void;
}

const FORM_ID = "custom-taxonomy-form";

const CustomTaxonomyEditDrawer = ({
  taxonomy,
  onClose,
  onDelete,
  ...props
}: CustomTaxonomyEditDrawerProps) => {
  const [updateCustomTaxonomy, { isLoading: isUpdating }] =
    useUpdateCustomTaxonomyMutation();

  const messageApi = useMessage();
  const { sortedCustomFieldDefinitionIds, idToCustomFieldDefinition } =
    useCustomFields({
      resourceType: taxonomy.fides_key,
    });

  const customFields = sortedCustomFieldDefinitionIds
    .map(
      (id) =>
        idToCustomFieldDefinition.get(id) as CustomFieldDefinitionWithId & {
          created_at: string;
        },
    )
    .sort((a, b) => (a.created_at ?? "").localeCompare(b.created_at ?? ""));

  const handleUpdate = async (values: TaxonomyUpdate) => {
    if (!taxonomy?.fides_key) {
      messageApi.error("Taxonomy not found");
      return;
    }
    const result = await updateCustomTaxonomy({
      fides_key: taxonomy.fides_key,
      ...values,
    });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }
    messageApi.success("Taxonomy updated successfully");
  };

  return (
    <DetailsDrawer
      title={`Edit ${taxonomy?.name}`}
      {...props}
      itemKey=""
      open={!!taxonomy}
      onClose={onClose}
      destroyOnHidden
      footer={
        <Flex justify="space-between" className="w-full">
          <Button onClick={onDelete}>Delete</Button>
          <Button
            type="primary"
            htmlType="submit"
            form={FORM_ID}
            loading={isUpdating}
          >
            Save
          </Button>
        </Flex>
      }
    >
      <CustomTaxonomyDetails
        taxonomy={taxonomy}
        onSubmit={handleUpdate}
        formId={FORM_ID}
        customFields={customFields}
      />
    </DetailsDrawer>
  );
};

export default CustomTaxonomyEditDrawer;
