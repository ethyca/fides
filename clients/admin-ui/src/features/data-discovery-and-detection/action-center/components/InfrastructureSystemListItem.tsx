import {
  Avatar,
  Button,
  Checkbox,
  Flex,
  Icons,
  List,
  Tag,
  Text,
  Tooltip,
  useMessage,
} from "fidesui";
import { useQueryState } from "nuqs";

import { getErrorMessage } from "~/features/common/helpers";
import { getBrandIconUrl, getDomain } from "~/features/common/utils";
import { INFRASTRUCTURE_DIFF_STATUS_COLOR } from "~/features/data-discovery-and-detection/action-center/constants";
import { tagRender } from "~/features/data-discovery-and-detection/action-center/fields/MonitorFieldListItem";
import { useUpdateInfrastructureSystemDataUsesMutation } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { DiffStatus, StagedResourceAPIResponse } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";
import InfrastructureClassificationSelect from "./InfrastructureClassificationSelect";
import { InfrastructureSystemActionsCell } from "./InfrastructureSystemActionsCell";

interface InfrastructureSystemListItemProps {
  item: StagedResourceAPIResponse;
  selected?: boolean;
  onSelect?: (key: string, selected: boolean) => void;
  monitorId: string;
  activeTab?: ActionCenterTabHash | null;
  allowIgnore?: boolean;
  allowRestore?: boolean;
  dataUsesDisabled?: boolean;
  onPromoteSuccess?: () => void;
}

export const InfrastructureSystemListItem = ({
  item,
  selected,
  onSelect,
  monitorId,
  activeTab,
  allowIgnore,
  allowRestore,
  dataUsesDisabled,
  onPromoteSuccess,
}: InfrastructureSystemListItemProps) => {
  const itemKey = item.urn;
  const systemName = item.name ?? "Uncategorized";

  const [, setStagedResourceUrn] = useQueryState("stagedResourceUrn");
  const messageApi = useMessage();

  const [updateDataUses] = useUpdateInfrastructureSystemDataUsesMutation();

  const handleUpdateDataUses = async (dataUses: string[]) => {
    const result = await updateDataUses({
      monitorId,
      dataUses,
      urn: itemKey,
    });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    }
  };

  const logoUrl = getBrandIconUrl(
    item.domain ?? getDomain(item.vendor_id ?? systemName),
    36,
  );

  const handleClick = () => {
    setStagedResourceUrn(itemKey);
  };

  const handleCheckboxChange = (checked: boolean) => {
    if (onSelect && itemKey) {
      onSelect(itemKey, checked);
    }
  };

  // Handle data use selection
  const handleSelectDataUse = (value: string) => {
    const currentDataUses = item.preferred_data_uses ?? [];
    if (!currentDataUses.includes(value)) {
      handleUpdateDataUses([...currentDataUses, value]);
    }
  };

  return (
    <List.Item
      key={itemKey}
      actions={[
        <InfrastructureSystemActionsCell
          key="actions"
          monitorId={monitorId}
          system={item}
          allowIgnore={allowIgnore}
          allowRestore={allowRestore}
          activeTab={activeTab}
          onPromoteSuccess={onPromoteSuccess}
        />,
      ]}
    >
      <List.Item.Meta
        avatar={
          <Flex align="center" gap="medium">
            <Checkbox
              checked={selected}
              onChange={(e) => handleCheckboxChange(e.target.checked)}
              onClick={(e) => e.stopPropagation()}
            />
            <Tooltip title={item.urn}>
              <Avatar
                src={logoUrl}
                shape="square"
                icon={
                  <Icons.TransformInstructions
                    style={{ color: "var(--fidesui-brand-minos)" }}
                    className="m-1 size-full"
                  />
                }
                className="bg-transparent"
                alt={systemName}
              />
            </Tooltip>
          </Flex>
        }
        title={
          <Flex gap="small" align="center" wrap="wrap">
            <Button
              type="text"
              size="small"
              onClick={handleClick}
              className="px-0"
            >
              <Text strong>{systemName}</Text>
            </Button>
            {item.diff_status === DiffStatus.MUTED && (
              <Tag color={INFRASTRUCTURE_DIFF_STATUS_COLOR[item.diff_status]}>
                Ignored
              </Tag>
            )}
          </Flex>
        }
        description={
          <>
            <Text>
              {"preferred_description" in item &&
              typeof item.preferred_description === "string"
                ? item.preferred_description
                : ""}
            </Text>
            <InfrastructureClassificationSelect
              mode="multiple"
              value={item.preferred_data_uses ?? []}
              urn={itemKey}
              tagRender={(props) => {
                // Show sparkle icon if the data use was auto-detected (in data_uses)
                // and not manually assigned (not in user_assigned_data_uses)
                const isAutoDetectedFromCompass = item.data_uses?.includes(
                  props.value as string,
                );

                const handleClose = () => {
                  const newDataUses =
                    item.preferred_data_uses?.filter(
                      (dataUse) => dataUse !== props.value,
                    ) ?? [];
                  handleUpdateDataUses(newDataUses);
                };

                return tagRender({
                  ...props,
                  isFromClassifier: isAutoDetectedFromCompass,
                  onClose: handleClose,
                });
              }}
              onSelectDataUse={handleSelectDataUse}
              disabled={dataUsesDisabled}
            />
          </>
        }
      />
    </List.Item>
  );
};
