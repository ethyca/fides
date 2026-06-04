import {
  Button,
  Checkbox,
  Flex,
  formatIsoLocation,
  Icons,
  isoStringToEntry,
  List,
  Tag,
  Text,
} from "fidesui";

import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import { PrivacyNoticeRegion, StagedResourceAPIResponse } from "~/types/api";

import { DiscoveryStatusDisplayNames } from "../constants";
import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";
import { DiscoveredAssetActionsCell } from "../tables/cells/DiscoveredAssetActionsCell";
import hasConsentComplianceIssue from "../utils/hasConsentComplianceIssue";
import WebsiteConsentSelect from "./WebsiteConsentSelect";

const formatLocation = (location: string): string => {
  const isoEntry = isoStringToEntry(location);
  return isoEntry
    ? formatIsoLocation({ isoEntry })
    : (PRIVACY_NOTICE_REGION_RECORD[location as PrivacyNoticeRegion] ??
        location);
};

export interface WebsiteAssetListItemProps {
  asset: StagedResourceAPIResponse;
  selected: boolean;
  onSelect: (urn: string, selected: boolean) => void;
  onNavigate: (asset: StagedResourceAPIResponse) => void;
  /** When true, inline system/consent edits are disabled. */
  readonly: boolean;
  /** When true, render the per-row actions cell (Approve/Ignore/Restore). */
  showActions: boolean;
  /** Whether the compliance status flag is enabled. */
  showComplianceStatus?: boolean;
  onTabChange: (tab: ActionCenterTabHash) => Promise<void>;
  showComplianceIssueDetails?: (asset: StagedResourceAPIResponse) => void;
}

export const WebsiteAssetListItem = ({
  asset,
  selected,
  onSelect,
  onNavigate,
  readonly,
  showActions,
  showComplianceStatus,
  onTabChange,
  showComplianceIssueDetails,
}: WebsiteAssetListItemProps) => {
  const {
    urn,
    name,
    resource_type: resourceType,
    domain,
    system: systemName,
    locations,
    consent_aggregated: consentAggregated,
  } = asset;

  // Only surface a red error tag when there's an actual compliance issue.
  const showComplianceError =
    showComplianceStatus && hasConsentComplianceIssue(consentAggregated);

  return (
    <List.Item
      key={urn}
      data-testid={`asset-row-${urn}`}
      actions={[
        domain ? (
          <Text key="domain" type="secondary" ellipsis={{ tooltip: domain }}>
            {domain}
          </Text>
        ) : null,
        locations && locations.length > 0 ? (
          <Flex key="locations" gap={4} wrap="wrap" className="max-w-60">
            {locations.map((location) => (
              <Tag key={location} color="default">
                {formatLocation(location)}
              </Tag>
            ))}
          </Flex>
        ) : null,
        showActions ? (
          // Fixed-width container reserves space for up to three icon buttons
          // (Approve, Ignore, + optional compliance) so the domain to its left
          // never shifts when the compliance button is/ isn't present.
          <div key="actions" className="ml-4 flex w-24 justify-end">
            <DiscoveredAssetActionsCell
              asset={asset}
              onTabChange={onTabChange}
              showComplianceIssueDetails={showComplianceIssueDetails}
              iconButtons
              primaryApprove
            />
          </div>
        ) : null,
      ].filter(Boolean)}
    >
      <List.Item.Meta
        avatar={
          <div className="ml-2">
            <Checkbox
              checked={selected}
              onChange={(e) => onSelect(urn, e.target.checked)}
              aria-label={`Select ${name}`}
            />
          </div>
        }
        title={
          <Flex gap={8} align="center" className="overflow-hidden">
            <Button
              type="text"
              size="small"
              className="-mx-2 overflow-hidden"
              onClick={() => onNavigate(asset)}
              data-testid="asset-name-btn"
            >
              <Text strong ellipsis={{ tooltip: name }}>
                {name}
              </Text>
            </Button>
            {resourceType && (
              <Text type="secondary" className="whitespace-nowrap font-normal">
                {resourceType}
              </Text>
            )}
            {/* System assignment is read-only here — edit it in the detail
                drawer (click the asset name) or via bulk "Assign system". */}
            {systemName ? (
              <Tag
                color="sandstone"
                icon={<Icons.TransformInstructions />}
                data-testid="asset-system"
                className="whitespace-nowrap"
              >
                {systemName}
              </Tag>
            ) : (
              <Tag
                color="warning"
                data-testid="asset-system"
                className="whitespace-nowrap"
              >
                Unassigned
              </Tag>
            )}
            {showComplianceError && (
              <Tag color="error" data-testid="compliance-error-tag">
                {DiscoveryStatusDisplayNames[consentAggregated!]}
              </Tag>
            )}
          </Flex>
        }
        description={<WebsiteConsentSelect asset={asset} readonly={readonly} />}
      />
    </List.Item>
  );
};

export default WebsiteAssetListItem;
