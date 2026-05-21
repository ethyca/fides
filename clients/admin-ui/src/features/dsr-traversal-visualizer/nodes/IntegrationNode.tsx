import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import classNames from "classnames";
import { Flex, Tag, Text } from "fidesui";
import { useMemo } from "react";

import { useConnectionLogo } from "~/features/common/hooks/useConnectionLogo";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import type { ConnectionConfigurationResponse } from "~/types/api";
import { ConnectionType } from "~/types/api/models/ConnectionType";

import {
  INTEGRATION_CARD_MIN_HEIGHT,
  REACHABILITY_COLOR,
  REACHABILITY_LABEL,
} from "../constants";
import { IntegrationNodeData } from "../types";
import styles from "./IntegrationNode.module.scss";

export type IntegrationNodeType = Node<IntegrationNodeData, "integration">;

export const IntegrationNode = ({ data }: NodeProps<IntegrationNodeType>) => {
  const {
    connection_key: connectionKey,
    connector_type: connectorType,
    saas_type: saasType,
    system,
    reachability,
    collection_count: collectionCount,
    data_categories: dataCategories,
  } = data;

  const { getDataCategoryDisplayName } = useTaxonomies();

  // Reuse the app-wide logo machinery so SaaS connectors pick up their
  // ``encoded_icon`` from ConnectionSystemTypeMap and websites fall through to
  // the brandfetch CDN. No new fetch wiring needed here -- the underlying
  // ``useGetAllConnectionTypesQuery`` is RTK-deduped across all nodes.
  const logoSource = useConnectionLogo(
    useMemo<ConnectionConfigurationResponse>(
      () =>
        ({
          connection_type: connectorType as ConnectionType,
          name: system?.name ?? null,
          key: connectionKey,
          saas_config: saasType
            ? {
                type: saasType,
                fides_key: connectionKey,
                name: system?.name ?? "",
              }
            : null,
          secrets: null,
        }) as ConnectionConfigurationResponse,
      [connectionKey, connectorType, saasType, system?.name],
    ),
  );

  return (
    <div
      className={classNames(styles.node, "relative w-80 box-border")}
      style={{ minHeight: INTEGRATION_CARD_MIN_HEIGHT }}
      data-testid={`integration-node:${connectionKey}`}
    >
      <Handle
        type="target"
        position={Position.Left}
        className={styles.handle}
      />
      <Flex align="flex-start" gap="small" className="px-4 py-3">
        <ConnectionTypeLogo data={logoSource} size={28} />
        <Flex vertical className="min-w-0 flex-1">
          <Text strong ellipsis={{ tooltip: system?.name ?? connectionKey }}>
            {system?.name ?? connectionKey}
          </Text>
          {system?.name && (
            <Text
              type="secondary"
              className={styles.metaText}
              ellipsis={{ tooltip: connectionKey }}
            >
              {connectionKey}
            </Text>
          )}
          {data.stage_via ? (
            <Text type="secondary" className={styles.stageVia}>
              via {data.stage_via}
            </Text>
          ) : null}
        </Flex>
      </Flex>
      <div className={classNames(styles.body, "px-4 py-3")}>
        <Flex justify="space-between" align="center" gap="small">
          <Text type="secondary" className={styles.metaText}>
            {collectionCount.traversed} of {collectionCount.total} collections
          </Text>
          <Tag color={REACHABILITY_COLOR[reachability]} className={styles.tag}>
            {REACHABILITY_LABEL[reachability]}
          </Tag>
        </Flex>
        {dataCategories.length > 0 && (
          <Flex gap={4} wrap className="mt-1.5">
            {dataCategories.slice(0, 3).map((dc) => (
              <Tag key={dc} className={styles.tag}>
                {getDataCategoryDisplayName(dc)}
              </Tag>
            ))}
            {dataCategories.length > 3 && (
              <Tag className={styles.tag}>+{dataCategories.length - 3}</Tag>
            )}
          </Flex>
        )}
      </div>
      <Handle
        type="source"
        position={Position.Right}
        className={styles.handle}
      />
    </div>
  );
};
