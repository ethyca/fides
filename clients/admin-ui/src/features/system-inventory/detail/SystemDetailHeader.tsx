import { Avatar, Button, Flex, Text, Title } from "fidesui";

import { getBrandIconUrl } from "~/features/common/utils";

import type { MockSystem } from "../types";

interface SystemDetailHeaderProps {
  system: MockSystem;
}

const SystemDetailHeader = ({ system }: SystemDetailHeaderProps) => {
  const initials = system.name
    .split(" ")
    .map((w) => w[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <Flex justify="space-between" align="flex-start" className="mb-4">
      <Flex gap="middle" align="center">
        <Avatar
          size={48}
          shape="square"
          src={system.logoDomain ? getBrandIconUrl(system.logoDomain, 96) : undefined}
          style={!system.logoDomain ? { backgroundColor: "#e6e6e8", color: "#53575c", fontSize: 16 } : undefined}
        >
          {!system.logoDomain ? initials : null}
        </Avatar>
        <div>
          <Title level={2} className="!mb-0">
            {system.name}
          </Title>
          <Text type="secondary">
            {system.system_type} &middot; {system.department} &middot;{" "}
            {system.responsibility}
          </Text>
        </div>
      </Flex>
      <Flex gap="small">
        <Button type="default">Export CSV</Button>
        <Button type="default">Edit</Button>
      </Flex>
    </Flex>
  );
};

export default SystemDetailHeader;
