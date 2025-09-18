import { EnableCell } from "~/features/common/table/v2/cells";
import { useUpdateCustomFieldDefinitionMutation } from "~/features/plus/plus.slice";
import { CustomFieldDefinitionWithId } from "~/types/api";

const EnableCustomFieldCellV2 = ({
  field,
  isDisabled,
}: {
  field: CustomFieldDefinitionWithId;
  isDisabled: boolean;
}) => {
  const [updateCustomFieldDefinitionTrigger, { isLoading }] =
    useUpdateCustomFieldDefinitionMutation();

  const onToggle = async (newValue: boolean) =>
    updateCustomFieldDefinitionTrigger({
      ...field,
      active: newValue,
    });

  return (
    <EnableCell
      enabled={field.active ?? false}
      onToggle={onToggle}
      title="Disable custom field"
      message="Are you sure you want to disable this custom field?"
      isDisabled={isDisabled}
      aria-label={field.active ? "Disable custom field" : "Enable custom field"}
      loading={isLoading}
    />
  );
};

export default EnableCustomFieldCellV2;
