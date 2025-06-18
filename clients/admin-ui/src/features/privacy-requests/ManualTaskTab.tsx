import { AntTypography as Typography, Box } from "fidesui";

const { Title, Text } = Typography;

const ManualTaskTab = () => {
  return (
    <Box p={6}>
      <Title level={2}>Manual Tasks</Title>

      <Text className="mb-4">
        This tab will contain the Manual Task management interface for DSR (Data
        Subject Request) workflows. It is only visible when the{" "}
        <code>alphaNewManualDSR</code> feature flag is enabled.
      </Text>

      <Box mt={6}>
        <Title level={4}>Planned Features:</Title>
        <ul className="mt-2 space-y-1 text-gray-600">
          <li>• Manual task assignment and tracking</li>
          <li>• Integration with DSR workflow automation</li>
          <li>• Task status monitoring and reporting</li>
          <li>• User notification and collaboration tools</li>
        </ul>
      </Box>
    </Box>
  );
};

export default ManualTaskTab;
