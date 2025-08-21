import { AntFlex, AntMessage as message, AntSelect, AntTag } from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { TagExpandableCell } from "~/features/common/table/cells";
import { ColumnState } from "~/features/common/table/cells/types";
import { useUpdateSystemMutation } from "~/features/system";
import { useMockUpdateSystemWithGroupsMutation } from "~/mocks/TEMP-system-groups/endpoints/systems";
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

  // const [updateSystemMutation] = useUpdateSystemMutation();
  const [updateSystemMutation] = useMockUpdateSystemWithGroupsMutation();

  const handleUpdate = async () => {
    setIsAdding(false);
    messageApi.open({
      key: UPDATE_SYSTEM_GROUPS_MSG_KEY,
      type: "loading",
      content: `Updating groups for ${system.name}...`,
    });
    const result = await updateSystemMutation({
      ...system,
      groups: pendingSelection,
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
      setTimeout(() => {
        messageApi.destroy(UPDATE_SYSTEM_GROUPS_MSG_KEY);
      }, 3000);
    }
  };

  return (
    <>
      {contextHolder}
      {!isAdding && (
        <AntFlex gap="small">
          <AntTag
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
        </AntFlex>
      )}
      {isAdding && (
        <AntFlex gap="small">
          <AntSelect
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
            onBlur={handleUpdate}
          />
        </AntFlex>
      )}
    </>
  );
};

export default SystemGroupCell;
