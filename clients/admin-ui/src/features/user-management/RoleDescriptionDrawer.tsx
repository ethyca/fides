import { Card, Flex, Typography } from "fidesui";

import { ROLES } from "~/features/user-management/constants";

const { Text, Title } = Typography;

const RoleDescriptionDrawer = () => (
  <div>
    <Title level={5} className="pb-4">
      Role Description
    </Title>
    <Flex vertical gap={16}>
      {ROLES.map((role) => (
        <Card key={role.roleKey} size="small">
          <Text strong>{role.label}</Text>
          <br />
          <Text type="secondary">{role.description}</Text>
        </Card>
      ))}
    </Flex>
  </div>
);

export default RoleDescriptionDrawer;
