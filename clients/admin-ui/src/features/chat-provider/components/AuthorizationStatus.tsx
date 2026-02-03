import { GreenCheckCircleIcon, Space, Tag, Typography } from "fidesui";

const { Text } = Typography;

interface AuthorizationStatusProps {
  authorized: boolean;
}

/**
 * Displays the authorization status with appropriate styling.
 * Uses Ant Design's semantic colors instead of hardcoded values.
 */
const AuthorizationStatus = ({ authorized }: AuthorizationStatusProps) => {
  if (authorized) {
    return (
      <Space data-testid="authorize-status">
        <GreenCheckCircleIcon />
        <Text type="success" strong>
          Authorized
        </Text>
      </Space>
    );
  }

  return (
    <Tag color="warning" data-testid="status-not-authorized">
      Not authorized
    </Tag>
  );
};

export default AuthorizationStatus;
