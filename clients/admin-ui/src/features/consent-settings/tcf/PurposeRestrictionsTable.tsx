import {
  AntButton as Button,
  AntColumnsType as ColumnsType,
  AntEmpty as Empty,
  AntFlex as Flex,
  AntTable as Table,
  AntTooltip as Tooltip,
  AntTypography as Typography,
} from "fidesui";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";

import { InfoCell } from "~/features/common/table/cells";
import {
  RangeEntry,
  TCFRestrictionType,
  TCFVendorRestriction,
} from "~/types/api";

import {
  RESTRICTION_TYPE_LABELS,
  VENDOR_RESTRICTION_LABELS,
} from "./constants";
import { PublisherRestrictionActionCell } from "./PublisherRestrictionActionCell";
import { PurposeRestrictionFormModal } from "./PurposeRestrictionFormModal";
import { useGetPublisherRestrictionsQuery } from "./tcf-config.slice";
import { PurposeRestriction } from "./types";

const { Text, Title } = Typography;

interface EmptyTableNoticeProps {
  onAdd: () => void;
}

const EmptyTableNotice = ({ onAdd }: EmptyTableNoticeProps) => (
  <Empty
    image={Empty.PRESENTED_IMAGE_SIMPLE}
    description={
      <Flex vertical align="center" gap="small">
        <Title level={5}>Add a restriction</Title>
        <Text className="max-w-lg" type="secondary">
          No restrictions have been added. By default, all vendors follow their
          declared legal basis unless a restriction is applied&mdash;add a
          restriction to override this behavior.
        </Text>
      </Flex>
    }
    data-testid="empty-table-notice"
  >
    <Button type="primary" onClick={onAdd}>
      Add +
    </Button>
  </Empty>
);

export const PurposeRestrictionsTable = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const router = useRouter();

  const purposeId = router.query.purpose_id
    ? parseInt(router.query.purpose_id as string, 10)
    : undefined;

  const configurationId = router.query.configuration_id as string;

  const { data: restrictionsData, isFetching } =
    useGetPublisherRestrictionsQuery(
      {
        configuration_id: configurationId,
        purpose_id: purposeId ?? 0,
      },
      { skip: !configurationId || !purposeId },
    );

  const transformedData: PurposeRestriction[] = useMemo(
    () =>
      (restrictionsData?.items ?? []).map((item) => ({
        id: item.id,
        restriction_type: item.restriction_type,
        vendor_restriction: item.vendor_restriction,
        vendor_ids:
          item.range_entries?.map((range: RangeEntry) =>
            range.end_vendor_id
              ? `${range.start_vendor_id}-${range.end_vendor_id}`
              : range.start_vendor_id.toString(),
          ) ?? [],
        purpose_id: item.purpose_id,
      })),
    [restrictionsData?.items],
  );

  const hasRestrictAllVendors = transformedData.some(
    (item) =>
      item.vendor_restriction === TCFVendorRestriction.RESTRICT_ALL_VENDORS,
  );

  const hasAllRestrictTypes = Object.values(TCFRestrictionType).every((type) =>
    transformedData.some((item) => item.restriction_type === type),
  );

  const columns: ColumnsType<PurposeRestriction> = useMemo(
    () => [
      {
        title: "Restriction type",
        key: "restriction_type",
        dataIndex: "restriction_type",
        render: (value: TCFRestrictionType) => RESTRICTION_TYPE_LABELS[value],
      },
      {
        title: "Vendor restriction",
        key: "vendor_restriction",
        dataIndex: "vendor_restriction",
        render: (value: TCFVendorRestriction) =>
          VENDOR_RESTRICTION_LABELS[value],
      },
      {
        title: (
          <InfoCell
            value="Vendors"
            tooltip="Specify which vendors the restriction applies to. You can apply restrictions to all vendors, specific vendors by their IDs, or allow only certain vendors while restricting the rest."
          />
        ),
        key: "vendor_ids",
        dataIndex: "vendor_ids",
        render: (value: string[]) => value.join(", ") || "All vendors",
      },
      {
        title: "Actions",
        key: "actions",
        width: 154,
        render: (_, record) => (
          <PublisherRestrictionActionCell
            currentValues={record}
            existingRestrictions={transformedData}
          />
        ),
      },
    ],
    [transformedData],
  );

  const handleOpenModal = () => {
    setIsModalOpen(true);
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
  };

  return (
    <Flex vertical gap="middle">
      <Flex justify="flex-end">
        <Tooltip
          title={
            // eslint-disable-next-line no-nested-ternary
            hasRestrictAllVendors
              ? 'Each vendor must have a unique restriction type. When "Restrict all vendors" is active for any restriction type, no other restrictions can be added.'
              : hasAllRestrictTypes
                ? "Each purpose must have a unique restriction type. When all restriction types are active, no other restrictions can be added. Use the 'Edit' button to change the vendor restrictions on each type."
                : undefined
          }
        >
          <Button
            type="primary"
            onClick={handleOpenModal}
            disabled={hasRestrictAllVendors || hasAllRestrictTypes}
            data-testid="add-restriction-button"
          >
            Add restriction +
          </Button>
        </Tooltip>
      </Flex>
      <Table
        dataSource={transformedData}
        columns={columns}
        rowKey="id"
        pagination={false}
        size="small"
        bordered
        loading={isFetching}
        locale={{
          emptyText: <EmptyTableNotice onAdd={handleOpenModal} />,
        }}
        data-testid="purpose-restrictions-table"
      />
      <PurposeRestrictionFormModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        existingRestrictions={transformedData}
        purposeId={purposeId}
        configurationId={configurationId}
      />
    </Flex>
  );
};
