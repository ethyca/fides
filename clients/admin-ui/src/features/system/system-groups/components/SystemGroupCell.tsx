import {
  AntButton as Button,
  AntFlex as Flex,
  AntFlexProps as FlexProps,
  AntMessage as message,
  AntSelect as Select,
  AntTag as Tag,
  Icons,
} from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { TagExpandableCell } from "~/features/common/table/cells";
import { ColumnState } from "~/features/common/table/cells/types";
import { useUpdateSystemMutation } from "~/features/system";
import { COLOR_VALUE_MAP } from "~/features/system/system-groups/colors";
import {
  BasicSystemResponseExtended,
  CustomTaxonomyColor,
  SystemGroup,
} from "~/types/api";
import { isErrorResult } from "~/types/errors";

const UPDATE_SYSTEM_GROUPS_MSG_KEY = "update-system-groups-msg";

interface SystemGroupCellProps extends Omit<FlexProps, "children"> {
  selectedGroups: SystemGroup[];
  allGroups: SystemGroup[];
  system: BasicSystemResponseExtended;
  columnState?: ColumnState;
}

const SystemGroupCell = ({
  selectedGroups,
  allGroups,
  system,
  columnState,
  ...props
}: SystemGroupCellProps) => {
  const [isAdding, setIsAdding] = useState(false);
  const [pendingSelection, setPendingSelection] = useState<string[]>(
    selectedGroups.map((group) => group.fides_key),
  );

  const [messageApi, contextHolder] = message.useMessage();

  const [updateSystemMutation] = useUpdateSystemMutation();

  const handleUpdate = async () => {
    setIsAdding(false);
    messageApi.open({
      key: UPDATE_SYSTEM_GROUPS_MSG_KEY,
      type: "loading",
      content: `Updating groups for ${system.name}...`,
    });
    const result = await updateSystemMutation({
      ...system,
      system_groups: pendingSelection,
    });
    if (isErrorResult(result)) {
      messageApi.open({
        key: UPDATE_SYSTEM_GROUPS_MSG_KEY,
        type: "error",
        content: getErrorMessage(
          result.error,
          "Failed to update system groups",
        ),
      });
    } else {
      messageApi.open({
        key: UPDATE_SYSTEM_GROUPS_MSG_KEY,
        type: "success",
        content: "System groups updated",
      });
    }
    setTimeout(() => {
      messageApi.destroy(UPDATE_SYSTEM_GROUPS_MSG_KEY);
    }, 3000);
  };

  return (
    <Flex gap="small" {...props}>
      {contextHolder}
      {!isAdding && (
        <>
          <Tag
            onClick={() => setIsAdding(true)}
            addable
            data-testid="group-add-btn"
            aria-label="Add group"
          />
          <TagExpandableCell
            values={selectedGroups.map(
              (group) =>
                group && {
                  label: group.name,
                  key: group.fides_key,
                  tagProps: {
                    color: group.label_color
                      ? `${COLOR_VALUE_MAP[group.label_color]}`
                      : undefined,
                    bordered:
                      group.label_color === CustomTaxonomyColor.TAXONOMY_WHITE,
                  },
                },
            )}
            columnState={columnState}
          />
        </>
      )}
      {isAdding && (
        <>
          <Select
            options={allGroups.map((group) => ({
              label: group.name,
              value: group.fides_key,
            }))}
            mode="tags"
            defaultValue={selectedGroups.map((group) => group.fides_key)}
            defaultOpen
            onChange={(value) => {
              setPendingSelection(value);
            }}
          />
          <Button icon={<Icons.Checkmark />} onClick={handleUpdate} />
        </>
      )}
    </Flex>
  );
};

export default SystemGroupCell;
