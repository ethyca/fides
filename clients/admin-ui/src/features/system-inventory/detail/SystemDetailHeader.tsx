import { TrashCan } from "@carbon/icons-react";
import { Avatar, Button, Flex, Modal, Text, Title } from "fidesui";
import { useRouter } from "next/router";
import { useState } from "react";

import { getBrandIconUrl } from "~/features/common/utils";

import type { MockSystem } from "../types";

interface SystemDetailHeaderProps {
  system: MockSystem;
}

const SystemDetailHeader = ({ system }: SystemDetailHeaderProps) => {
  const router = useRouter();
  const [deleteOpen, setDeleteOpen] = useState(false);
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
          src={system.logoUrl ?? (system.logoDomain ? getBrandIconUrl(system.logoDomain, 96) : undefined)}
          style={!system.logoDomain && !system.logoUrl ? { backgroundColor: "#e6e6e8", color: "#53575c", fontSize: 16 } : undefined}
        >
          {!system.logoDomain && !system.logoUrl ? initials : null}
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
        <Button
          type="text"
          danger
          icon={<TrashCan size={16} />}
          onClick={() => setDeleteOpen(true)}
        />
        <Button type="default">Export CSV</Button>
      </Flex>

      <Modal
        title="Delete system"
        open={deleteOpen}
        onCancel={() => setDeleteOpen(false)}
        onOk={() => {
          setDeleteOpen(false);
          router.push("/system-inventory");
        }}
        okText="Delete"
        okButtonProps={{ danger: true }}
        width={440}
      >
        <Text>
          Are you sure you want to delete <Text strong>{system.name}</Text>? This action cannot be undone. All associated data, integrations, and history will be permanently removed.
        </Text>
      </Modal>
    </Flex>
  );
};

export default SystemDetailHeader;
