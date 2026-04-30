import { Card, Flex, Text } from "fidesui";

const LegendPanel = () => (
  <Card
    size="small"
    style={{ position: "absolute", bottom: 16, left: 16, zIndex: 10 }}
    data-testid="visualizer-legend"
  >
    <Flex vertical gap={4}>
      <Text strong style={{ fontSize: 12 }}>
        Legend
      </Text>
      <Text type="secondary" style={{ fontSize: 11 }}>
        ● Integration ▲ Manual task ◆ Identity
      </Text>
      <Text type="secondary" style={{ fontSize: 11 }}>
        — depends on - - - gates
      </Text>
    </Flex>
  </Card>
);

export default LegendPanel;
