import { ColumnsType, CUSTOM_TAG_COLOR, Flex, Tag, Typography } from "fidesui";
import { useMemo, useState } from "react";

import { LinkCell } from "~/features/common/table/cells/LinkCell";

import {
  CONSUMER_TYPE_UI_LABELS,
  PLATFORM_LABELS,
  type StatusFilterValue,
} from "./constants";
import type { ConsumerType, MockDataConsumer } from "./types";
import { useDataConsumers } from "./useDataConsumers";

const PURPOSE_DISPLAY_MAX = 2;

const useDataConsumersTable = () => {
  const { consumers, metrics, unresolvedCount } = useDataConsumers();

  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState<ConsumerType | null>(null);
  const [statusFilter, setStatusFilter] = useState<StatusFilterValue | null>(
    null,
  );
  const [platformFilter, setPlatformFilter] = useState<string | null>(null);

  const filteredConsumers = useMemo(() => {
    const lowerSearch = search.toLowerCase();
    return consumers.filter((c) => {
      if (
        search &&
        !c.name.toLowerCase().includes(lowerSearch) &&
        !c.identifier.toLowerCase().includes(lowerSearch)
      ) {
        return false;
      }
      if (typeFilter && c.type !== typeFilter) {
        return false;
      }
      if (statusFilter === "has_violations" && c.violationCount <= 0) {
        return false;
      }
      if (statusFilter === "no_purposes" && c.purposes.length > 0) {
        return false;
      }
      if (
        statusFilter === "healthy" &&
        (c.violationCount > 0 || c.purposes.length === 0)
      ) {
        return false;
      }
      if (platformFilter && c.platform !== platformFilter) {
        return false;
      }
      return true;
    });
  }, [consumers, search, typeFilter, statusFilter, platformFilter]);

  const columns: ColumnsType<MockDataConsumer> = useMemo(
    () => [
      {
        title: "Consumer",
        key: "name",
        render: (_, { name, identifier, id }) => (
          <Flex vertical gap={2}>
            <LinkCell href={`/data-consumers/${id}`}>{name}</LinkCell>
            <Typography.Text type="secondary" style={{ fontSize: 12 }}>
              {identifier}
            </Typography.Text>
          </Flex>
        ),
      },
      {
        title: "Type",
        key: "type",
        width: 140,
        render: (_, { type }) => (
          <Tag>{CONSUMER_TYPE_UI_LABELS[type] ?? type}</Tag>
        ),
      },
      {
        title: "Platform",
        key: "platform",
        width: 140,
        render: (_, { platform }) =>
          platform ? (PLATFORM_LABELS[platform] ?? platform) : "—",
      },
      {
        title: "Purposes",
        key: "purposes",
        render: (_, { purposes }) => {
          if (purposes.length === 0) {
            return (
              <Typography.Text type="warning">
                No purposes assigned
              </Typography.Text>
            );
          }
          const displayed = purposes.slice(0, PURPOSE_DISPLAY_MAX);
          const overflow = purposes.length - PURPOSE_DISPLAY_MAX;
          return (
            <Typography.Text>
              {displayed.join(", ")}
              {overflow > 0 && (
                <Typography.Text type="secondary">
                  {` +${overflow}`}
                </Typography.Text>
              )}
            </Typography.Text>
          );
        },
      },
      {
        title: "Violations",
        key: "violations",
        width: 120,
        render: (_, { violationCount, purposes }) => {
          if (purposes.length === 0) {
            return <Tag color={CUSTOM_TAG_COLOR.WARNING}>No purposes</Tag>;
          }
          if (violationCount > 0) {
            return (
              <Tag color={CUSTOM_TAG_COLOR.ERROR}>{violationCount}</Tag>
            );
          }
          return <Tag color={CUSTOM_TAG_COLOR.SUCCESS}>0</Tag>;
        },
      },
    ],
    [],
  );

  return {
    consumers,
    filteredConsumers,
    columns,
    metrics,
    unresolvedCount,
    search,
    setSearch,
    typeFilter,
    setTypeFilter,
    statusFilter,
    setStatusFilter,
    platformFilter,
    setPlatformFilter,
  };
};

export default useDataConsumersTable;
