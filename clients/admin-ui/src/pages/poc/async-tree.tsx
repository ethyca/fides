import {
  Layout,
  Row,
  TreeDataNode,
  Typography,
} from "fidesui";
import AsyncTree, {
  AsyncTreeProps,
} from "~/features/data-discovery-and-detection/action-center/AsyncTree";
import { useLazyGetMonitorTreeQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { DatastoreStagedResourceTreeAPIResponse } from "~/types/api/models/DatastoreStagedResourceTreeAPIResponse";
import { PaginatedResponse, PaginationQueryParams } from "~/types/query-params";
import { Page_DatastoreStagedResourceAPIResponse_ } from "~/types/api/models/Page_DatastoreStagedResourceAPIResponse_";
import { Page_DatastoreStagedResourceTreeAPIResponse_, StagedResourceTypeValue } from "~/types/api";

const { Content } = Layout;
const { Title } = Typography;

export const FormsPOC = () => {
  const [trigger, _result] = useLazyGetMonitorTreeQuery();
  const MONITOR_CONFIG_ID = "mypizzatest";

  const transformResponseToNode = (
    response: Page_DatastoreStagedResourceTreeAPIResponse_,
  ): TreeDataNode[] =>
    response.items.map((item) => ({
      key: item.urn,
      title: item.name,
      isLeaf: item.resource_type === StagedResourceTypeValue.FIELD || !item.has_grandchildren
    }));

  const loadData: AsyncTreeProps["loadData"] =
    async ({ page, size }, key) =>
      new Promise(async (resolve) => {
        const { data } = await trigger({
          monitor_config_id: MONITOR_CONFIG_ID,
          staged_resource_urn: key?.toString(),
          include_descendant_details: true,
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
      <AsyncTree loadData={loadData} />
    </Content>
  );
};

export default FormsPOC;
