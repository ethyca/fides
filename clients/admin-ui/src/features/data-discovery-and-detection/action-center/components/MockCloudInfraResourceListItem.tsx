import {
  Avatar,
  Button,
  Checkbox,
  DefaultOptionType,
  Flex,
  Icons,
  List,
  Space,
  Tag,
  Tooltip,
} from "fidesui";
import { MouseEventHandler, useRef, useState } from "react";

import { LabeledText } from "~/features/privacy-requests/dashboard/list-item/components/LabeledText";
import { AddNewSystemModal } from "~/features/system/AddNewSystemModal";
import { DiffStatus } from "~/types/api";
import { CloudInfraStagedResource } from "~/types/api/models/CloudInfraStagedResource";

import { INFRASTRUCTURE_DIFF_STATUS_COLOR } from "../constants";
import {
  getServiceIconUrl,
  getServiceLabel,
} from "../utils/cloudInfraServiceInfo";
import { MockSystemSelect } from "./MockSystemSelect";
import { SystemTagIcon } from "./SystemLeadingIcon";

interface MockCloudInfraResourceListItemProps {
  item: CloudInfraStagedResource;
  selected: boolean;
  onSelect: (urn: string, selected: boolean) => void;
  assignedSystems: DefaultOptionType[];
  onAddSystem: (urn: string, system: DefaultOptionType) => void;
  onRemoveSystem: (
    urn: string,
    systemValue: DefaultOptionType["value"],
  ) => void;
  onApprove: (urn: string) => void;
  onIgnore: (urn: string) => void;
  onRestore: (urn: string) => void;
  onOpenDetails: (resource: CloudInfraStagedResource) => void;
}

export const MockCloudInfraResourceListItem = ({
  item,
  selected,
  onSelect,
  assignedSystems,
  onAddSystem,
  onRemoveSystem,
  onApprove,
  onIgnore,
  onRestore,
  onOpenDetails,
}: MockCloudInfraResourceListItemProps) => {
  const [isAssigning, setIsAssigning] = useState(false);
  const [isNewSystemModalOpen, setIsNewSystemModalOpen] = useState(false);
  const isOpeningModalRef = useRef(false);

  const name = item.name ?? "Unnamed resource";
  const serviceLabel = getServiceLabel(item.service);
  const isMuted = item.diff_status === DiffStatus.MUTED;
  const isApproved = item.diff_status === DiffStatus.MONITORED;
  const isRemoved = item.diff_status === DiffStatus.REMOVAL;

  const hasAssigned = assignedSystems.length > 0;
  const approveDisabled = !hasAssigned || isMuted;
  let approveTooltip = "Approve";
  if (!hasAssigned) {
    approveTooltip = "Assign a system before approving";
  } else if (isMuted) {
    approveTooltip = "Restore before approving";
  }

  const tagEntries = item.tags ? Object.entries(item.tags) : [];

  const onAddNewSystemClick: MouseEventHandler<HTMLButtonElement> = (e) => {
    e.preventDefault();
    isOpeningModalRef.current = true;
    setIsNewSystemModalOpen(true);
  };

  return (
    <>
      <List.Item
        key={item.urn}
        actions={[
          <Space key="actions" size={32}>
            {item.location && <Tag color="default">{item.location}</Tag>}
            <Space size="small">
              {isMuted ? (
                <Tooltip title="Restore">
                  <Button
                    size="small"
                    icon={<Icons.View />}
                    aria-label="Restore"
                    data-testid={`restore-btn-${item.urn}`}
                    onClick={() => onRestore(item.urn)}
                  />
                </Tooltip>
              ) : (
                <Tooltip title="Ignore">
                  <Button
                    size="small"
                    icon={<Icons.ViewOff />}
                    aria-label="Ignore"
                    data-testid={`ignore-btn-${item.urn}`}
                    onClick={() => onIgnore(item.urn)}
                  />
                </Tooltip>
              )}
              <Tooltip title={approveTooltip}>
                <Button
                  size="small"
                  type={approveDisabled ? "default" : "primary"}
                  icon={<Icons.Checkmark />}
                  aria-label="Approve"
                  disabled={approveDisabled}
                  data-testid={`approve-btn-${item.urn}`}
                  onClick={() => onApprove(item.urn)}
                />
              </Tooltip>
            </Space>
          </Space>,
        ]}
      >
        <List.Item.Meta
          avatar={
            <Flex align="center" gap="middle">
              <Checkbox
                checked={selected}
                onChange={(e) => onSelect(item.urn, e.target.checked)}
                onClick={(e) => e.stopPropagation()}
                data-testid={`select-${item.urn}`}
              />
              <Avatar
                src={getServiceIconUrl(item.service)}
                shape="square"
                icon={
                  <Icons.Layers
                    style={{ color: "var(--fidesui-brand-minos)" }}
                    className="m-1 size-full"
                  />
                }
                className="bg-transparent"
                alt={name}
              />
            </Flex>
          }
          title={
            <Flex gap="small" align="center" wrap="wrap">
              <button
                type="button"
                onClick={() => onOpenDetails(item)}
                data-testid={`open-details-${item.urn}`}
                className="cursor-pointer p-0 text-left font-semibold text-[var(--fidesui-minos)] hover:underline"
              >
                {name}
              </button>
              {item.service && <Tag color="sandstone">{serviceLabel}</Tag>}
              {isMuted && (
                <Tag color={INFRASTRUCTURE_DIFF_STATUS_COLOR[DiffStatus.MUTED]}>
                  Ignored
                </Tag>
              )}
              {isApproved && (
                <Tag
                  color={INFRASTRUCTURE_DIFF_STATUS_COLOR[DiffStatus.MONITORED]}
                >
                  Approved
                </Tag>
              )}
              {isRemoved && (
                <Tag
                  color={INFRASTRUCTURE_DIFF_STATUS_COLOR[DiffStatus.REMOVAL]}
                >
                  Removed
                </Tag>
              )}
            </Flex>
          }
          description={
            <Flex vertical gap={8}>
              {tagEntries.length > 0 && (
                <Flex gap="middle" wrap="wrap">
                  {tagEntries.map(([key, value]) => (
                    <LabeledText key={key} label={key}>
                      {value}
                    </LabeledText>
                  ))}
                </Flex>
              )}
              <Flex
                vertical
                gap="small"
                align="start"
                style={{ minHeight: 32 }}
              >
                {isAssigning ? (
                  // Multi-select (mirrors the detail drawer): tick several
                  // systems at once; untick to remove. Stays open until blur.
                  <MockSystemSelect
                    autoFocus
                    defaultOpen
                    mode="multiple"
                    labelInValue
                    placeholder="Search systems..."
                    style={{ minWidth: 240, maxWidth: "100%" }}
                    value={assignedSystems}
                    onAddSystem={onAddNewSystemClick}
                    onSelect={(_, option) => onAddSystem(item.urn, option)}
                    onDeselect={(value) => {
                      const optionValue =
                        typeof value === "object" &&
                        value !== null &&
                        "value" in value
                          ? (value as DefaultOptionType).value
                          : value;
                      onRemoveSystem(item.urn, optionValue);
                    }}
                    onDropdownVisibleChange={(open) => {
                      if (open) {
                        return;
                      }
                      setTimeout(() => {
                        if (isOpeningModalRef.current) {
                          isOpeningModalRef.current = false;
                          return;
                        }
                        setIsAssigning(false);
                      }, 0);
                    }}
                    data-testid={`system-select-${item.urn}`}
                  />
                ) : (
                  <Flex gap="small" wrap="wrap" align="center">
                    <Tooltip
                      title={hasAssigned ? "Add system" : "Assign system"}
                    >
                      <Button
                        size="small"
                        type="text"
                        icon={<Icons.Add />}
                        onClick={() => setIsAssigning(true)}
                        aria-label={
                          hasAssigned ? "Add system" : "Assign system"
                        }
                        data-testid={`assign-system-btn-${item.urn}`}
                        className="flex-none"
                      />
                    </Tooltip>
                    {assignedSystems.map((system) => (
                      <Tag
                        key={String(system.value)}
                        color="white"
                        bordered
                        closable
                        onClose={() => onRemoveSystem(item.urn, system.value)}
                        data-testid={`assigned-system-${item.urn}-${system.value}`}
                      >
                        <Flex align="center" gap="small">
                          <SystemTagIcon value={system.value} />
                          {system.label}
                        </Flex>
                      </Tag>
                    ))}
                  </Flex>
                )}
              </Flex>
            </Flex>
          }
        />
      </List.Item>
      {isNewSystemModalOpen && (
        <AddNewSystemModal
          isOpen
          onClose={() => {
            setIsNewSystemModalOpen(false);
            isOpeningModalRef.current = false;
            setIsAssigning(false);
          }}
          onSuccessfulSubmit={(fidesKey, systemName) => {
            setIsNewSystemModalOpen(false);
            isOpeningModalRef.current = false;
            onAddSystem(item.urn, { label: systemName, value: fidesKey });
            setIsAssigning(false);
          }}
          toastOnSuccess
        />
      )}
    </>
  );
};
