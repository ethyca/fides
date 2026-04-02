import { Icons, Space, Tag, Typography } from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";

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
        <Icons.CheckmarkFilled color={palette.FIDESUI_SUCCESS} />
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
