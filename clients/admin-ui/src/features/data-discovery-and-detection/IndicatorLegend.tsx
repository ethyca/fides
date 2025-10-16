import {
  AntCol as Col,
  AntPopover as Popover,
  AntRow as Row,
  AntSpace as Space,
  Icons,
} from "fidesui";

import {
  AdditionIndicator,
  ChangeIndicator,
  ClassificationIndicator,
  MonitoredIndicator,
  MutedIndicator,
  RemovalIndicator,
} from "~/features/data-discovery-and-detection/statusIndicators";

export const IndicatorLegend = () => {
  const content = (
    <div className="mx-4 max-w-[300px] py-3">
      <Row gutter={[16, 8]}>
        <Col span={12}>
          <Space>
            <ChangeIndicator />
            <div>Change detected</div>
          </Space>
        </Col>
        <Col span={12}>
          <Space>
            <ClassificationIndicator />
            <div>Data labeled</div>
          </Space>
        </Col>
        <Col span={12}>
          <Space>
            <MonitoredIndicator />
            <div>Monitoring</div>
          </Space>
        </Col>
        <Col span={12}>
          <Space>
            <AdditionIndicator />
            <div>Addition detected</div>
          </Space>
        </Col>
        <Col span={12}>
          <Space>
            <MutedIndicator />
            <div>Unmonitored</div>
          </Space>
        </Col>
        <Col span={12}>
          <Space>
            <RemovalIndicator />
            <div>Removal detected</div>
          </Space>
        </Col>
      </Row>
    </div>
  );

  return (
    <Popover
      content={content}
      title="Activity legend:"
      trigger={["hover", "focus"]}
    >
      <Icons.HelpFilled
        style={{ color: "var(--fidesui-neutral-400)", cursor: "pointer" }}
        tabIndex={0}
      />
    </Popover>
  );
};
