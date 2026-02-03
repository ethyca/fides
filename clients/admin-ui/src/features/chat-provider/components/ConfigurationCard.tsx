import { Card, Flex, Space, Typography } from "fidesui";
import { ReactNode } from "react";

const { Title } = Typography;

interface ConfigurationCardProps {
  title: string;
  icon?: ReactNode;
  children: ReactNode;
  maxWidth?: number;
}

/**
 * Reusable card component for configuration forms.
 * Uses Ant Design Card with consistent styling.
 */
const ConfigurationCard = ({
  title,
  icon,
  children,
  maxWidth = 720,
}: ConfigurationCardProps) => {
  return (
    <Card
      title={
        icon ? (
          <Space>
            {icon}
            <Title level={5} style={{ margin: 0 }}>
              {title}
            </Title>
          </Space>
        ) : (
          <Title level={5} style={{ margin: 0 }}>
            {title}
          </Title>
        )
      }
      style={{ maxWidth }}
      className="mt-6"
    >
      {children}
    </Card>
  );
};

export default ConfigurationCard;
