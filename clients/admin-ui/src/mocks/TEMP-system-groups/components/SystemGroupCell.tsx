import { AntFlex, AntMessage as message, AntSelect, AntTag } from "fidesui";
import { useState } from "react";
import { getErrorMessage } from "~/features/common/helpers";
import { TagExpandableCell } from "~/features/common/table/cells";
import { useMockUpdateSystemWithGroupsMutation } from "~/mocks/TEMP-system-groups/endpoints/systems";
import {
  SystemGroup,
  SystemResponseWithGroups,
  SystemUpsertWithGroups,
} from "~/mocks/TEMP-system-groups/types";
import { isErrorResult } from "~/types/errors";

const SystemGroupCell = ({
  selectedGroups,
  allGroups,
  system,
}: {
  selectedGroups: SystemGroup[];
  allGroups: SystemGroup[];
  system: SystemResponseWithGroups;
}) => {
  const [isAdding, setIsAdding] = useState(false);
  const [pendingSelection, setPendingSelection] = useState<string[]>(
    selectedGroups.map((group) => group.fides_key),
  );

  const [messageApi, contextHolder] = message.useMessage();

  const [updateSystemMutation] = useMockUpdateSystemWithGroupsMutation();

  const handleUpdate = async () => {
    setIsAdding(false);
    const result = await updateSystemMutation({
      ...system,
      groups: pendingSelection,
    });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success("System groups updated");
    }
  };

  return (
    <>
      {contextHolder}
      {!isAdding && (
        <AntFlex gap={8}>
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
                  tagProps: { color: group.color },
                },
            )}
            columnState={{
              isWrapped: true,
            }}
            bordered={false}
          />
        </AntFlex>
      )}
      {isAdding && (
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
      )}
    </>
  );
};

export default SystemGroupCell;
