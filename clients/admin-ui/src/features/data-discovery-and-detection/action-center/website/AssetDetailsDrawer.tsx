import {
  Collapse,
  Descriptions,
  Flex,
  Form,
  formatIsoLocation,
  Icons,
  isoStringToEntry,
  Paragraph,
  Spin,
  Tag,
  Text,
} from "fidesui";
import { groupBy } from "lodash";
import { useMemo, useState } from "react";

import { SystemSelect } from "~/features/common/dropdown/SystemSelect";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { truncateUrl } from "~/features/common/utils";
import { AddNewSystemModal } from "~/features/system/AddNewSystemModal";
import {
  ConsentStatus,
  PrivacyNoticeRegion,
  StagedResourceAPIResponse,
} from "~/types/api";

import { useGetConsentBreakdownQuery } from "../action-center.slice";
import {
  DiscoveryErrorStatuses,
  DiscoveryStatusDescriptions,
  DiscoveryStatusDisplayNames,
} from "../constants";
import { DetailsDrawer } from "../fields/DetailsDrawer";
import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";
import { DiscoveredAssetActionsCell } from "../tables/cells/DiscoveredAssetActionsCell";
import WebsiteConsentSelect from "./WebsiteConsentSelect";

const ALL_CONSENT_STATUSES = Object.values(ConsentStatus);

const formatLocation = (location: string): string => {
  const isoEntry = isoStringToEntry(location);
  return isoEntry
    ? formatIsoLocation({ isoEntry })
    : (PRIVACY_NOTICE_REGION_RECORD[location as PrivacyNoticeRegion] ??
        location);
};

/**
 * "Assets detected on" — a collapse, one panel per page the asset was detected
 * on, surfacing the locations and any compliance issue for that page.
 */
const AssetsDetectedOn = ({
  stagedResource,
}: {
  stagedResource: StagedResourceAPIResponse;
}) => {
  const { data, isFetching, isError } = useGetConsentBreakdownQuery({
    stagedResourceUrn: stagedResource.urn,
    statuses: ALL_CONSENT_STATUSES,
    page: 1,
    // The consent endpoint caps `size` at 100; an asset's page/location rows
    // stay well under that.
    size: 100,
  });

  const byPage = useMemo(
    () => groupBy(data?.items ?? [], (row) => row.page),
    [data?.items],
  );
  const pages = Object.keys(byPage);

  if (isFetching) {
    return <Spin size="small" />;
  }
  // Nothing detected for this asset — render nothing (no empty header).
  if (isError || !pages.length) {
    return null;
  }

  const collapseItems = pages.map((page) => {
    const rows = byPage[page];
    const errorRow = rows.find((row) =>
      DiscoveryErrorStatuses.includes(row.status),
    );
    return {
      key: page,
      label: (
        <Flex
          justify="space-between"
          align="center"
          gap="small"
          className="overflow-hidden"
        >
          <Text ellipsis={{ tooltip: page }}>{truncateUrl(page, 40)}</Text>
          {errorRow && (
            <Tag color="error">
              {DiscoveryStatusDisplayNames[errorRow.status]}
            </Tag>
          )}
        </Flex>
      ),
      children: (
        <Flex vertical gap="small">
          <div>
            <Text strong>Locations:</Text>
            <Flex wrap="wrap" gap="small" className="mt-1">
              {rows.map((row) => {
                const isErr = DiscoveryErrorStatuses.includes(row.status);
                return (
                  <Tag
                    key={`${row.location}-${row.status}`}
                    color={isErr ? "error" : "white"}
                    bordered
                  >
                    {formatLocation(row.location)}
                    {isErr && (
                      <Icons.WarningAltFilled
                        className="ml-1"
                        style={{
                          color: "var(--fidesui-color-error)",
                          verticalAlign: "text-bottom",
                        }}
                      />
                    )}
                  </Tag>
                );
              })}
            </Flex>
          </div>
          {errorRow && (
            <div>
              <Text strong>
                {`Compliance issue: ${DiscoveryStatusDisplayNames[errorRow.status]}`}
              </Text>
              <Paragraph type="secondary" className="mb-0 mt-1">
                {DiscoveryStatusDescriptions[errorRow.status]}
              </Paragraph>
            </div>
          )}
        </Flex>
      ),
    };
  });

  return (
    <Flex vertical gap="small">
      <Text strong>Assets detected on</Text>
      <Collapse items={collapseItems} />
    </Flex>
  );
};

interface AssetDetailsDrawerProps {
  asset?: StagedResourceAPIResponse;
  open: boolean;
  onClose: () => void;
  readonly: boolean;
  onTabChange: (tab: ActionCenterTabHash) => Promise<void>;
  onSystemAssign?: (
    asset: StagedResourceAPIResponse,
    fidesKey: string,
    systemName: string,
    isNewSystem?: boolean,
  ) => Promise<boolean>;
}

export const AssetDetailsDrawer = ({
  asset,
  open,
  onClose,
  readonly,
  onTabChange,
  onSystemAssign,
}: AssetDetailsDrawerProps) => {
  const locations = asset?.locations ?? [];
  const [isNewSystemModalOpen, setIsNewSystemModalOpen] = useState(false);

  return (
    <DetailsDrawer
      itemKey={asset?.urn ?? ""}
      title={asset?.name ?? null}
      titleIcon={<Icons.Document />}
      open={open}
      onClose={onClose}
      footer={
        asset && !readonly ? (
          <Flex justify="flex-end">
            <DiscoveredAssetActionsCell
              asset={asset}
              hideComplianceWarning
              onTabChange={async (tab) => {
                await onTabChange(tab);
                onClose();
              }}
            />
          </Flex>
        ) : undefined
      }
    >
      {asset ? (
        <Flex vertical gap="middle">
          {/* Fixed, read-only facts in a small descriptions block */}
          <Descriptions
            size="small"
            column={1}
            bordered
            items={[
              {
                key: "type",
                label: "Asset type",
                children: asset.resource_type ?? "—",
              },
              {
                key: "locations",
                label: "Locations",
                children: locations.length
                  ? locations.map(formatLocation).join(", ")
                  : "—",
              },
            ]}
          />

          <Form layout="vertical">
            <Form.Item label="System">
              <SystemSelect
                key={asset.urn}
                className="w-full"
                placeholder="Select a system"
                defaultValue={
                  asset.user_assigned_system_key ||
                  asset.system_key ||
                  undefined
                }
                disabled={readonly}
                onAddSystem={() => setIsNewSystemModalOpen(true)}
                onSelect={(value, option) =>
                  onSystemAssign?.(
                    asset,
                    value as string,
                    (option?.label as string) ?? (value as string),
                  )
                }
              />
            </Form.Item>
            <Form.Item label="Categories of consent" className="mb-0">
              <WebsiteConsentSelect
                asset={asset}
                readonly={readonly}
                bordered
              />
            </Form.Item>
          </Form>

          {isNewSystemModalOpen && (
            <AddNewSystemModal
              isOpen
              onClose={() => setIsNewSystemModalOpen(false)}
              onSuccessfulSubmit={(fidesKey, systemName) => {
                onSystemAssign?.(asset, fidesKey, systemName, true);
                setIsNewSystemModalOpen(false);
              }}
            />
          )}

          <AssetsDetectedOn stagedResource={asset} />
        </Flex>
      ) : null}
    </DetailsDrawer>
  );
};

export default AssetDetailsDrawer;
