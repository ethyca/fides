import { useState, Key } from "react";
import {
  Layout,
  Row,
  TreeDataNode,
  Typography,
  Tooltip,
  Badge
} from "fidesui";
import AsyncTree, {
} from "~/features/data-discovery-and-detection/action-center/AsyncTree";
import { AsyncTreeProps } from "~/features/data-discovery-and-detection/action-center/AsyncTree/types"
import { useLazyGetMonitorTreeQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { MAP_DATASTORE_RESOURCE_TYPE_TO_ICON, MAP_TREE_RESOURCE_CHANGE_INDICATOR_TO_STATUS_INFO } from "~/features/data-discovery-and-detection/action-center/fields/MonitorFields.const";
import { DiffStatus, Page_DatastoreStagedResourceTreeAPIResponse_, StagedResourceTypeValue } from "~/types/api";

const { Content } = Layout;
const { Title } = Typography;

export const FormsPOC = () => {
  const [trigger, _result] = useLazyGetMonitorTreeQuery();
  const MONITOR_CONFIG_ID = "Custom_Structure_Monitor_41";
  const [selectedKeys, setSelectedKeys] = useState<Key[]>()

  /**
   * @description the primary of interacting with the async data tree is through request/response patterns
   */
  const transformResponseToNode = (
    response: Page_DatastoreStagedResourceTreeAPIResponse_,
  ): TreeDataNode[] =>
    response.items.map((item) => ({
      key: item.urn,
      title: item.name,
      disabled: item.diff_status === DiffStatus.MUTED,
      icon: () => {
        const resourceType = Object.values(StagedResourceTypeValue).find((key) => key === item.resource_type)
        const IconComponent = resourceType
          ? MAP_DATASTORE_RESOURCE_TYPE_TO_ICON[resourceType] : undefined;
        const statusInfo = item.update_status
          ? MAP_TREE_RESOURCE_CHANGE_INDICATOR_TO_STATUS_INFO[
          item.update_status
          ]
          : undefined;

        return IconComponent ? (
          <Tooltip title={statusInfo?.tooltip}>
            <Badge
              className="h-full"
              offset={[0, 5]}
              color={statusInfo?.color}
            // dot={shouldShowBadgeDot(treeNode)}
            >
              <IconComponent className="h-full" />
            </Badge>
          </Tooltip>
        )
          : undefined
      },
      isLeaf: item.resource_type === StagedResourceTypeValue.FIELD
      // ||
      // !item.has_grandchildren,
    }));

  const loadData: AsyncTreeProps["loadData"] =
    async ({ page, size }, key) =>
      new Promise(async (resolve) => {
        const { data } = await trigger({
          monitor_config_id: MONITOR_CONFIG_ID,
          staged_resource_urn: key?.toString(),
          page,
          size,
        });

        resolve({
          items: data ? transformResponseToNode(data) : [],
          total: data?.total ?? 0,
          size: data?.size ?? 0,
          pages: data?.pages ?? 0,
          page
        });
      });

  return (
    <Content className="overflow-auto px-10 py-6">
      <Row>
        <Title>Async Tree POC</Title>
      </Row>
      <AsyncTree
        loadData={loadData}
        actions={{
          nodeActions: {
            "Copy": {
              label: "Copy",
              callback: (keys) => alert(keys),
              disabled: () => false
            }
          },
          primaryAction: "Copy"
        }}
        pageSize={5}
        onSelect={(keys) => setSelectedKeys(keys)}
        selectedKeys={selectedKeys}
        showFooter
        taxonomy={['resource', 'resources']}
      />
    </Content>
  );
};

export default FormsPOC;
