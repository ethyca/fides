import {
  AntButton as Button,
  AntFlex as Flex,
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
import { BasicSystemResponseExtended, SystemGroup } from "~/types/api";
import { isErrorResult } from "~/types/errors";

const UPDATE_SYSTEM_GROUPS_MSG_KEY = "update-system-groups-msg";

const SystemGroupCell = ({
  selectedGroups,
  allGroups,
  system,
  columnState,
}: {
  selectedGroups: SystemGroup[];
  allGroups: SystemGroup[];
  system: BasicSystemResponseExtended;
  columnState?: ColumnState;
}) => {
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
    <>
      {contextHolder}
      {!isAdding && (
        <Flex gap="small">
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
                  tagProps: { color: group.label_color },
                },
            )}
            bordered={false}
            columnState={columnState}
          />
        </Flex>
      )}
      {isAdding && (
        <Flex gap="small">
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
        </Flex>
      )}
    </>
  );
};

export default SystemGroupCell;
