import { Button, Flex, Tabs, useMessage } from "fidesui";

import { useCustomFields } from "~/features/common/custom-fields";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { FIDES_KEY_RESOURCE_TYPE_MAP } from "~/features/custom-fields/constants";
import { DetailsDrawer } from "~/features/data-discovery-and-detection/action-center/fields/DetailsDrawer";
import { DetailsDrawerProps } from "~/features/data-discovery-and-detection/action-center/fields/DetailsDrawer/types";
import TaxonomyDetails from "~/features/taxonomy/components/TaxonomyDetails";
import TaxonomyHistory from "~/features/taxonomy/components/TaxonomyHistory";
import { TaxonomyTypeEnum } from "~/features/taxonomy/constants";
import { useUpdateCustomTaxonomyMutation } from "~/features/taxonomy/taxonomy.slice";
import { CustomFieldDefinitionWithId } from "~/types/api";
import { TaxonomyResponse } from "~/types/api/models/TaxonomyResponse";
import { TaxonomyUpdate } from "~/types/api/models/TaxonomyUpdate";

interface TaxonomyEditDrawerProps extends Omit<DetailsDrawerProps, "itemKey"> {
  taxonomy: TaxonomyResponse;
  onDelete: () => void;
}

const FORM_ID = "custom-taxonomy-form";

const TaxonomyEditDrawer = ({
  taxonomy,
  onClose,
  onDelete,
  ...props
}: TaxonomyEditDrawerProps) => {
  const [updateCustomTaxonomy, { isLoading: isUpdating }] =
    useUpdateCustomTaxonomyMutation();

  const messageApi = useMessage();
  const { sortedCustomFieldDefinitionIds, idToCustomFieldDefinition } =
    useCustomFields({
      resourceType:
        FIDES_KEY_RESOURCE_TYPE_MAP[taxonomy.fides_key] ?? taxonomy.fides_key,
    });

  const isCustom = !Object.values(TaxonomyTypeEnum).includes(
    taxonomy.fides_key as TaxonomyTypeEnum,
  );

  const customFields = sortedCustomFieldDefinitionIds
    .map(
      (id) =>
        idToCustomFieldDefinition.get(id) as CustomFieldDefinitionWithId & {
          created_at: string;
        },
    )
    .sort((a, b) => (a.created_at ?? "").localeCompare(b.created_at ?? ""));

  const handleUpdate = async (values: TaxonomyUpdate) => {
    if (!taxonomy.fides_key) {
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
        isCustom && (
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
        )
      }
    >
      <Tabs
        items={[
          {
            label: "Details",
            key: "details",
            children: (
              <TaxonomyDetails
                taxonomy={taxonomy}
                onSubmit={handleUpdate}
                formId={FORM_ID}
                customFields={customFields}
                isCustom={isCustom}
              />
            ),
          },
          {
            label: "History",
            key: "history",
            children: <TaxonomyHistory taxonomyKey={taxonomy.fides_key} />,
          },
        ]}
      />
    </DetailsDrawer>
  );
};

export default TaxonomyEditDrawer;
