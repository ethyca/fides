/* eslint-disable react/no-unstable-nested-components */
import { Badge, Icons, Tooltip, TreeDataNode } from "fidesui";
import { useRouter } from "next/router";
import { Key } from "react";

import { useLazyGetMonitorTreeQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { AsyncTree } from "~/features/data-discovery-and-detection/action-center/AsyncTree";
import {
  NodeAction,
  TreeActions,
} from "~/features/data-discovery-and-detection/action-center/AsyncTree/types";
import {
  DEFAULT_FILTER_STATUSES,
  MAP_DATASTORE_RESOURCE_TYPE_TO_ICON,
  MAP_DIFF_STATUS_TO_STATUS_INFO,
} from "~/features/data-discovery-and-detection/action-center/fields/MonitorFields.const";
import { shouldShowBadgeDot } from "~/features/data-discovery-and-detection/action-center/fields/treeUtils";
import { DiffStatus, StagedResourceTypeValue } from "~/types/api";
import { CursorPage_DatastoreStagedResourceTreeAPIResponse_ } from "~/types/api/models/CursorPage_DatastoreStagedResourceTreeAPIResponse_";
import { FieldActionType } from "~/types/api/models/FieldActionType";

import {
  FIELD_ACTION_LABEL,
  RESOURCE_ACTIONS,
} from "./fields/FieldActions.const";
import { intoDiffStatus } from "./fields/utils";
import { DatastorePageSettings } from "./types";

interface AsyncMonitorTreeProps
  extends TreeActions<Record<string, NodeAction<TreeDataNode>>> {
  setSelectedNodeKeys: (keys: Key[]) => void;
  selectedNodeKeys: Key[];
}

export const AsyncMonitorTree = ({
  setSelectedNodeKeys,
  selectedNodeKeys,
  nodeActions,
  primaryAction,
  showApproved,
  showIgnored,
}: AsyncMonitorTreeProps & DatastorePageSettings) => {
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);
  const [trigger] = useLazyGetMonitorTreeQuery();

  /**
   * @description the primary of interacting with the async data tree is through request/response patterns
   */
  const transformResponseToNode = (
    response: CursorPage_DatastoreStagedResourceTreeAPIResponse_,
  ): TreeDataNode[] =>
    response.items.map((item) => ({
      key: item.urn,
      title: item.name,
      disabled: item.diff_status === DiffStatus.MUTED,
      actions: Object.fromEntries(
        RESOURCE_ACTIONS.map((action) => [
          action,
          {
            label: FIELD_ACTION_LABEL[action],
            /** Logic for this should exist on the BE */
            disabled: () => {
              const classifyable = [
                StagedResourceTypeValue.SCHEMA,
                StagedResourceTypeValue.TABLE,
                StagedResourceTypeValue.ENDPOINT,
                StagedResourceTypeValue.FIELD,
              ].some((resourceType) => resourceType === item.resource_type);

              if (
                (action === FieldActionType.PROMOTE_REMOVALS &&
                  item.diff_status === DiffStatus.REMOVAL) ||
                (action === FieldActionType.CLASSIFY &&
                  classifyable &&
                  item.diff_status !== DiffStatus.MUTED) ||
                (action === FieldActionType.MUTE &&
                  item.diff_status !== DiffStatus.MUTED) ||
                (action === FieldActionType.UN_MUTE &&
                  item.diff_status === DiffStatus.MUTED)
              ) {
                return false;
              }

              return true;
            },
            callback: async () =>
              nodeActions[action].callback(
                [item.urn],
                [
                  {
                    key: item.urn,
                    title: item.name,
                    disabled: item.diff_status === DiffStatus.MUTED,
                  },
                ],
              ),
          },
        ]),
      ),
      icon: () => {
        const resourceType = Object.values(StagedResourceTypeValue).find(
          (key) => key === item.resource_type,
        );

        const resourceIcon = resourceType
          ? MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[resourceType]
          : undefined;

        const IconComponent =
          item.diff_status === DiffStatus.MUTED ? Icons.ViewOff : resourceIcon;

        const statusInfo = item.diff_status
          ? MAP_DIFF_STATUS_TO_STATUS_INFO[item.diff_status]
          : undefined;

        return IconComponent ? (
          <Tooltip title={statusInfo?.tooltip}>
            <Badge
              className="h-full"
              offset={[0, 5]}
              color={statusInfo?.color}
              dot={shouldShowBadgeDot(item)}
            >
              <IconComponent className="h-full" />
            </Badge>
          </Tooltip>
        ) : undefined;
      },
      isLeaf: item.resource_type === StagedResourceTypeValue.FIELD,
    }));

  return (
    <div className="grid h-full grid-rows-[1fr_minmax(max-content,max-content)] gap-6 overflow-x-hidden">
      <AsyncTree
        loadData={({ cursor, size }, key) =>
          new Promise((resolve) => {
            trigger({
              monitor_config_id: monitorId,
              staged_resource_urn: key?.toString(),
              diff_status: [
                ...DEFAULT_FILTER_STATUSES.flatMap(intoDiffStatus),
                ...(showIgnored ? intoDiffStatus("Ignored") : []),
                ...(showApproved ? intoDiffStatus("Approved") : []),
              ],
              cursor,
              size,
            }).then(({ data }) =>
              resolve({
                items: data ? transformResponseToNode(data) : [],
                total: data?.total ?? 0,
                current_page: data?.current_page ?? undefined,
                next_page: data?.next_page ?? undefined,
              }),
            );
          })
        }
        refreshData={(key, childKeys) =>
          new Promise((resolve) => {
            trigger({
              monitor_config_id: monitorId,
              staged_resource_urn: key?.toString(),
              diff_status: [
                ...DEFAULT_FILTER_STATUSES.flatMap(intoDiffStatus),
                ...(showIgnored ? intoDiffStatus("Ignored") : []),
                ...(showApproved ? intoDiffStatus("Approved") : []),
              ],
              child_staged_resource_urns: childKeys?.map((childKey) =>
                childKey.toString(),
              ),
              size: childKeys?.length,
            }).then(({ data }) =>
              resolve({
                items: data ? transformResponseToNode(data) : [],
                total: data?.total ?? 0,
                current_page: data?.current_page ?? undefined,
                next_page: data?.next_page ?? undefined,
              }),
            );
          })
        }
        actions={{ primaryAction, nodeActions }}
        // pageSize={2}
        onSelect={(keys) => setSelectedNodeKeys(keys)}
        selectedKeys={selectedNodeKeys}
        showFooter
        taxonomy={["resource", "resources"]}
        queryKeys={[String(showIgnored), String(showApproved)]}
        className="overflow-scroll overflow-x-hidden"
      />
    </div>
  );
};
