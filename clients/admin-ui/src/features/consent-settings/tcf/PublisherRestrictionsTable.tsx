import { Button, ColumnsType, Skeleton, Table, Tag, Typography } from "fidesui";
import NextLink from "next/link";
import React, { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectPurposes } from "~/features/common/purpose.slice";
import { InfoCell } from "~/features/common/table/cells";
import { MappedPurpose, TCFConfigurationDetail } from "~/types/api";

import {
  FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS,
  RESTRICTION_TYPE_LABELS,
} from "./constants";

const { Text } = Typography;

interface PublisherRestrictionsTableProps {
  className?: string;
  config?: TCFConfigurationDetail;
  isLoading?: boolean;
}

export const PublisherRestrictionsTable = ({
  className,
  config,
  isLoading,
}: PublisherRestrictionsTableProps): JSX.Element => {
  const { purposes } = useAppSelector(selectPurposes);

  const dataSource = useMemo(() => Object.values(purposes), [purposes]);

  const columns: ColumnsType<MappedPurpose> = useMemo(
    () => [
      {
        title: "TCF purpose",
        key: "purpose",
        render: (_, record) => (
          <>
            Purpose {record.id}: {record.name}
          </>
        ),
      },
      {
        title: (
          <InfoCell
            value="Restrictions"
            tooltip="Restrictions control how vendors are permitted to process data for specific purposes. Fides supports three restriction types: Purpose Restriction to completely disallow data processing for a purpose, Require Consent to allow processing only with explicit user consent, and Require Legitimate Interest to allow processing based on legitimate business interest unless the user objects."
          />
        ),
        key: "restrictions",
        dataIndex: "id",
        render: (purposeId: number) => {
          if (isLoading) {
            return <Skeleton paragraph={false} active />;
          }
          const types =
            config?.restriction_types_per_purpose?.[purposeId] ?? [];
          if (types.length === 0) {
            return "none";
          }
          if (types.length === 1) {
            return (
              <Text className="whitespace-nowrap">
                {RESTRICTION_TYPE_LABELS[types[0]]}
              </Text>
            );
          }
          return (
            <Text className="whitespace-nowrap">
              {types.length} restrictions
            </Text>
          );
        },
        onCell: (record) =>
          ({
            "data-testid": `restriction-type-cell-${record.id}`,
          }) as React.TdHTMLAttributes<HTMLTableCellElement>,
      },
      {
        title: (
          <InfoCell
            value="Flexible"
            tooltip='Indicates whether the legal basis for this purpose can be overridden by publisher restrictions. If marked "No," the purpose has a fixed legal basis defined by the TCF and cannot be changed.'
          />
        ),
        key: "flexible",
        dataIndex: "id",
        width: 100,
        render: (purposeId: number) =>
          FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS.includes(purposeId) ? (
            <Tag color="error" data-testid={`flexibility-tag-${purposeId}`}>
              No
            </Tag>
          ) : (
            <Tag color="success" data-testid={`flexibility-tag-${purposeId}`}>
              Yes
            </Tag>
          ),
      },
      {
        title: "Actions",
        key: "actions",
        width: 100,
        render: (_, record) => (
          <NextLink
            href={`/settings/consent/${config?.id}/${record.id}`}
            passHref
            legacyBehavior
          >
            <Button
              size="small"
              data-testid={`edit-restriction-btn-${record.id}`}
            >
              Edit
            </Button>
          </NextLink>
        ),
      },
    ],
    [config, isLoading],
  );

  return (
    <Table
      className={className}
      dataSource={dataSource}
      columns={columns}
      rowKey="id"
      pagination={false}
      size="small"
      bordered
      data-testid="publisher-restrictions-table"
    />
  );
};
