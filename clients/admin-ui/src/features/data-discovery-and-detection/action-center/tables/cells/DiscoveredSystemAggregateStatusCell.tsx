import {
  AntFlex as Flex,
  AntTooltip as Tooltip,
  AntTypography as Typography,
} from "fidesui";
import NextLink from "next/link";

import { STATUS_INDICATOR_MAP } from "~/features/data-discovery-and-detection/statusIndicators";
import { SystemStagedResourcesAggregateRecord } from "~/types/api";

import { DiscoveryStatusIcon } from "../../DiscoveryStatusIcon";

const { Link, Text } = Typography;

interface DiscoveredSystemStatusCellProps {
  system: SystemStagedResourcesAggregateRecord;
  rowClickUrl?: (record: SystemStagedResourcesAggregateRecord) => string;
}

export const DiscoveredSystemStatusCell = ({
  system,
  rowClickUrl,
}: DiscoveredSystemStatusCellProps) => {
  const url = rowClickUrl?.(system);
  return (
    <Flex align="center">
      {!system.system_key && (
        <Tooltip title="New system">
          {/* icon has to be wrapped in a span for the tooltip to work */}
          <span>{STATUS_INDICATOR_MAP.Change}</span>
        </Tooltip>
      )}
      <Flex align="center" gap={4} className="max-w-[250px] flex-nowrap">
        {url ? (
          <NextLink href={url} passHref legacyBehavior>
            {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
            <Link
              size="sm"
              strong
              ellipsis
              onClick={(e) => e.stopPropagation()}
              data-testid="system-name-link"
            >
              {system.name || "Uncategorized assets"}
            </Link>
          </NextLink>
        ) : (
          <Text size="sm" strong ellipsis data-testid="system-name-text">
            {system.name || "Uncategorized assets"}
          </Text>
        )}
        <DiscoveryStatusIcon consentStatus={system.consent_status} />
      </Flex>
    </Flex>
  );
};
