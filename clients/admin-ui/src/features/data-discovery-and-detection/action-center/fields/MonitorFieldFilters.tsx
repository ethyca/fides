import {
  AntButton as Button,
  AntCheckbox as Checkbox,
  AntCol as Col,
  AntForm as Form,
  AntRow as Row,
  AntSpace as Space,
} from "fidesui";
import { capitalize } from "lodash";

import { useGetDatastoreFiltersQuery } from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import { ConfidenceScoreRange } from "~/types/api/models/ConfidenceScoreRange";

import { RESOURCE_STATUS, useMonitorFieldsFilters } from "./useFilters";

export const MonitorFieldFilters = ({
  resourceStatus,
  setResourceStatus,
  confidenceScore,
  setConfidenceScore,
  dataCategory,
  setDataCategory,
  reset,
  monitorId,
}: ReturnType<typeof useMonitorFieldsFilters> & { monitorId: string }) => {
  const { data: datastoreFilterResponse } = useGetDatastoreFiltersQuery({
    monitor_config_id: monitorId,
  });

  return (
    <div
      /** Note: limitation of using tailwind is not having access to all of ant design's style attributes
       * ex: large border radius variant and secondary box shadow
       */
      className="rounded-[var(--ant-border-radius)] bg-[var(--ant-color-bg-base)] shadow-md"
    >
      <Space size="middle" className="p-[var(--ant-padding)]">
        <Form layout="vertical">
          <Form.Item label="Status" className="w-min whitespace-nowrap">
            <Checkbox.Group
              value={resourceStatus || []}
              onChange={(value) =>
                setResourceStatus(value.length > 0 ? value : null)
              }
            >
              <Row>
                {RESOURCE_STATUS.map((label) => {
                  return (
                    <Col span={24} key={label}>
                      <Checkbox value={label}>{label}</Checkbox>
                    </Col>
                  );
                })}
              </Row>
            </Checkbox.Group>
          </Form.Item>
          <Form.Item
            label="Confidence Score"
            className="w-min whitespace-nowrap"
          >
            <Checkbox.Group
              value={confidenceScore || []}
              onChange={(scores) =>
                setConfidenceScore(scores.length > 0 ? scores : null)
              }
            >
              <Row>
                {Object.values(ConfidenceScoreRange).map((cs) => {
                  return (
                    <Col span={24} key={cs}>
                      <Checkbox value={cs}>{capitalize(cs)}</Checkbox>
                    </Col>
                  );
                })}
              </Row>
            </Checkbox.Group>
          </Form.Item>
          {datastoreFilterResponse?.data_category &&
            datastoreFilterResponse?.data_category?.length > 0 && (
              <Form.Item
                label="Data Category"
                className="w-min whitespace-nowrap"
              >
                <Checkbox.Group
                  value={dataCategory || []}
                  onChange={(values) =>
                    setDataCategory(values.length > 0 ? values : null)
                  }
                >
                  <Row>
                    {datastoreFilterResponse.data_category.map((value) => {
                      return (
                        <Col span={24} key={value}>
                          <Checkbox value={value}>{capitalize(value)}</Checkbox>
                        </Col>
                      );
                    })}
                  </Row>
                </Checkbox.Group>
              </Form.Item>
            )}
          <Button
            onClick={() => {
              reset();
            }}
          >
            Clear
          </Button>
        </Form>
      </Space>
    </div>
  );
};
