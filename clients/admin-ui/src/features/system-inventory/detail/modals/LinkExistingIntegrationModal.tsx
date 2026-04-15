import { Checkbox, Flex, Input, Modal, Select, Spin, Tag, Text, useMessage } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import { useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import ConnectionTypeLogo, {
  connectionLogoFromConfiguration,
  connectionLogoFromSystemType,
} from "~/features/datastore-connections/ConnectionTypeLogo";
import { useGetAllDatastoreConnectionsQuery } from "~/features/datastore-connections/datastore-connection.slice";
import { useGetAllConnectionTypesQuery } from "~/features/connection-type";
import { useSetSystemLinksMutation } from "~/features/integrations/system-links.slice";
import { ActionType, ConnectionType } from "~/types/api";

const CAPABILITY_OPTIONS = [
  { label: "Access", value: ActionType.ACCESS },
  { label: "Erasure", value: ActionType.ERASURE },
  { label: "Update", value: ActionType.UPDATE },
];

const DSR_TYPES = new Set([
  ConnectionType.POSTGRES,
  ConnectionType.MYSQL,
  ConnectionType.REDSHIFT,
  ConnectionType.SNOWFLAKE,
  ConnectionType.BIGQUERY,
  ConnectionType.DYNAMODB,
  ConnectionType.MONGODB,
  ConnectionType.MARIADB,
  ConnectionType.TIMESCALE,
  ConnectionType.SCYLLA,
  ConnectionType.GOOGLE_CLOUD_SQL_MYSQL,
  ConnectionType.GOOGLE_CLOUD_SQL_POSTGRES,
  ConnectionType.RDS_MYSQL,
  ConnectionType.RDS_POSTGRES,
  ConnectionType.TEST_DATASTORE,
]);

function inferActions(
  connectionType: ConnectionType,
  configured: ActionType[] | null | undefined,
): ActionType[] {
  if (configured && configured.length > 0) {
    return configured.filter((a) => a !== ActionType.CONSENT);
  }
  if (DSR_TYPES.has(connectionType)) {
    return [ActionType.ACCESS, ActionType.ERASURE];
  }
  return [];
}


interface LinkExistingIntegrationModalProps {
  open: boolean;
  onClose: () => void;
  systemFidesKey: string;
}

const LinkExistingIntegrationModal = ({
  open,
  onClose,
  systemFidesKey,
}: LinkExistingIntegrationModalProps) => {
  const [selected, setSelected] = useState<string[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [search, setSearch] = useState("");
  const [capabilityFilter, setCapabilityFilter] = useState<ActionType | null>(
    null,
  );

  const [setSystemLinks] = useSetSystemLinksMutation();
  const message = useMessage();

  const { data, isFetching } = useGetAllDatastoreConnectionsQuery({
    page: 1,
    size: 100,
    orphaned_from_system: true,
  });

  const { data: connectionTypesData } = useGetAllConnectionTypesQuery({});
  const connectionTypes = useMemo(
    () => connectionTypesData?.items || [],
    [connectionTypesData],
  );

  const items = data?.items ?? [];

  const enriched = useMemo(
    () =>
      items.map((item) => {
        const isSaas =
          item.connection_type === ConnectionType.SAAS && !!item.saas_config?.type;

        const connectionTypeMap = isSaas
          ? connectionTypes.find((c) => c.identifier === item.saas_config?.type)
          : undefined;

        const logoSource = connectionTypeMap
          ? connectionLogoFromSystemType(connectionTypeMap)
          : connectionLogoFromConfiguration(item);

        const typeName =
          connectionTypeMap?.human_readable ??
          (isSaas ? item.saas_config?.type : item.connection_type) ??
          item.connection_type;

        return { item, logoSource, typeName };
      }),
    [items, connectionTypes],
  );

  const filtered = useMemo(
    () =>
      enriched.filter(({ item, typeName }) => {
        if (search) {
          const q = search.toLowerCase();
          const nameMatch = (item.name ?? item.key).toLowerCase().includes(q);
          const typeMatch = typeName.toLowerCase().includes(q);
          if (!nameMatch && !typeMatch) return false;
        }
        if (
          capabilityFilter &&
          !item.enabled_actions?.includes(capabilityFilter)
        ) {
          return false;
        }
        return true;
      }),
    [enriched, search, capabilityFilter],
  );

  const resetAndClose = () => {
    setSelected([]);
    setSearch("");
    setCapabilityFilter(null);
    onClose();
  };

  const handleLink = async () => {
    if (selected.length === 0) return;
    setSubmitting(true);
    try {
      await Promise.all(
        selected.map((connectionKey) =>
          setSystemLinks({
            connectionKey,
            body: { links: [{ system_fides_key: systemFidesKey }] },
          }).unwrap(),
        ),
      );
      message.success(
        `Linked ${selected.length} integration${selected.length !== 1 ? "s" : ""}.`,
      );
      resetAndClose();
    } catch (error) {
      const rtkError = error as Parameters<typeof getErrorMessage>[0];
      message.error(getErrorMessage(rtkError));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Modal
      title="Link existing integration"
      open={open}
      onCancel={resetAndClose}
      onOk={handleLink}
      okText={`Link${selected.length ? ` ${selected.length}` : ""} integration${selected.length !== 1 ? "s" : ""}`}
      okButtonProps={{
        disabled: selected.length === 0 || submitting,
        loading: submitting,
      }}
      width={780}
    >
      <Text type="secondary" className="mb-3 block">
        Choose one or more integrations to connect to this system. Only
        integrations not yet linked to a system are shown.
      </Text>

      {isFetching ? (
        <Flex justify="center" className="py-8">
          <Spin />
        </Flex>
      ) : items.length === 0 ? (
        <Flex justify="center" className="py-6">
          <Text type="secondary">No available integrations to link.</Text>
        </Flex>
      ) : (
        <Flex vertical gap={10}>
          {/* Search + filter bar */}
          <Flex gap={8}>
            <Input
              placeholder="Search by name or type..."
              value={search}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                setSearch(e.target.value)
              }
              allowClear
              size="small"
              className="flex-1"
            />
            <Select
              aria-label="Filter by capability"
              placeholder="All capabilities"
              value={capabilityFilter}
              onChange={(v) => setCapabilityFilter((v as ActionType) ?? null)}
              allowClear
              size="small"
              className="w-[180px]"
              options={CAPABILITY_OPTIONS}
            />
          </Flex>

          {/* Table */}
          <div className="max-h-[380px] overflow-y-auto rounded border border-solid border-[#f0f0f0]">
            {/* Header */}
            <Flex
              className="sticky top-0 border-b border-solid border-[#f0f0f0] px-3 py-2"
              style={{ backgroundColor: palette.FIDESUI_NEUTRAL_75 }}
            >
              {/* spacer to match checkbox column */}
              <div className="mr-3 w-4 flex-shrink-0" />
              <Text
                strong
                className="w-[38%] text-[10px] uppercase tracking-wider"
              >
                Integration
              </Text>
              <Text
                strong
                className="w-[22%] text-[10px] uppercase tracking-wider"
              >
                Type
              </Text>
              <Text
                strong
                className="w-[28%] text-[10px] uppercase tracking-wider"
              >
                Capabilities
              </Text>
              <Text
                strong
                className="w-[12%] text-[10px] uppercase tracking-wider"
              >
                Status
              </Text>
            </Flex>

            {/* Rows */}
            {filtered.map(({ item, logoSource, typeName }) => {
              const isSelected = selected.includes(item.key);
              const isDisabled = item.disabled ?? false;

              return (
                <Flex
                  key={item.key}
                  align="center"
                  className={`cursor-pointer border-b border-solid border-[#f5f5f5] px-3 py-2 hover:bg-[#fafafa] ${
                    isSelected ? "bg-blue-50" : ""
                  }`}
                  onClick={() =>
                    setSelected(
                      isSelected
                        ? selected.filter((k) => k !== item.key)
                        : [...selected, item.key],
                    )
                  }
                >
                  {/* Checkbox */}
                  <div className="mr-3 flex-shrink-0">
                    <Checkbox checked={isSelected} />
                  </div>

                  {/* Logo + Name */}
                  <Flex align="center" gap={8} className="w-[38%] min-w-0">
                    <ConnectionTypeLogo data={logoSource} size={24} />
                    <Text
                      strong={isSelected}
                      className="truncate text-xs"
                      title={item.name ?? item.key}
                    >
                      {item.name ?? item.key}
                    </Text>
                  </Flex>

                  {/* Type */}
                  <Text type="secondary" className="w-[22%] truncate text-xs">
                    {typeName}
                  </Text>

                  {/* Capabilities */}
                  <div className="w-[28%]">
                    {(() => {
                      const actions = inferActions(
                        item.connection_type,
                        item.enabled_actions,
                      );
                      return (
                        <Text type="secondary" className="text-xs">
                          {actions.length > 0 ? actions.join(", ") : "—"}
                        </Text>
                      );
                    })()}
                  </div>

                  {/* Status */}
                  <Flex align="center" className="w-[12%]">
                    <Tag
                      color={isDisabled ? "default" : "success"}
                      bordered={false}
                      className="!text-[10px]"
                    >
                      {isDisabled ? "Disabled" : "Active"}
                    </Tag>
                  </Flex>
                </Flex>
              );
            })}

            {filtered.length === 0 && (
              <Flex justify="center" className="py-6">
                <Text type="secondary" className="text-xs">
                  No integrations match your filters.
                </Text>
              </Flex>
            )}
          </div>
        </Flex>
      )}
    </Modal>
  );
};

export default LinkExistingIntegrationModal;
