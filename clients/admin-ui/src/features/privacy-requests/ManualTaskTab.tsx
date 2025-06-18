import { AntTypography as Typography, Box } from "fidesui";

const { Title, Text } = Typography;

const ManualTaskTab = () => {
  return (
    <Box p={6}>
      <Title level={2}>Manual Tasks</Title>
      <Text>
        This is a placeholder for the Manual Task functionality. This tab is
        only visible when the alphaNewManualDSR feature flag is enabled.
      </Text>
      <Box mt={4}>
        <Text type="secondary">
          Future implementation will include:
          <br />• Manual task management interface
          <br />• Task assignment and tracking
          <br />• Integration with DSR workflow
        </Text>
      </Box>
    </Box>
  );
};

export default ManualTaskTab;
