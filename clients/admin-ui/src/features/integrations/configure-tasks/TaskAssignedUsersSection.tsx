import {
  AntButton as Button,
  AntSelect as Select,
  AntTable as Table,
  AntTypography as Typography,
  Box,
  Flex,
  Icons,
  Text,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import {
  useAssignUsersToManualTaskMutation,
  useGetManualTaskConfigQuery,
} from "~/features/datastore-connections/connection-manual-tasks.slice";
import { useGetAllUsersQuery } from "~/features/user-management/user-management.slice";

type Props = {
  connectionKey: string;
  onManageSecureAccess: () => void;
};

const TaskAssignedUsersSection = ({
  connectionKey,
  onManageSecureAccess,
}: Props) => {
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [userToAssign, setUserToAssign] = useState<string | undefined>();
  const [isSaving, setIsSaving] = useState(false);

  const { data: manualTaskConfig } = useGetManualTaskConfigQuery(
    { connectionKey },
    { skip: !connectionKey },
  );
  const [assignUsersToManualTask] = useAssignUsersToManualTaskMutation();
  const { data: usersData } = useGetAllUsersQuery({
    page: 1,
    size: 100,
    username: "",
  });

  useEffect(() => {
    if (manualTaskConfig?.assigned_users) {
      const emails = manualTaskConfig.assigned_users
        .map((u) => u.email_address)
        .filter((e): e is string => Boolean(e));
      setSelectedUsers(emails);
    }
  }, [manualTaskConfig]);

  const availableUserOptions = useMemo(() => {
    const users = usersData?.items ?? [];
    return users
      .filter(
        (u: any) => u.email_address && !selectedUsers.includes(u.email_address),
      )
      .map((u: any) => ({
        label: `${u.first_name ?? ""} ${u.last_name ?? ""}`.trim()
          ? `${u.first_name ?? ""} ${u.last_name ?? ""} (${u.email_address})`
          : `${u.email_address}`,
        value: u.email_address,
      }));
  }, [usersData, selectedUsers]);

  const handleAssign = async () => {
    if (!userToAssign) {
      return;
    }
    try {
      setIsSaving(true);
      const updated = Array.from(
        new Set([...(selectedUsers ?? []), userToAssign]),
      );
      await assignUsersToManualTask({
        connectionKey,
        userIds: updated,
      }).unwrap();
      setSelectedUsers(updated);
      setUserToAssign(undefined);
    } finally {
      setIsSaving(false);
    }
  };

  const handleRemove = async (email: string) => {
    try {
      setIsSaving(true);
      const updated = (selectedUsers ?? []).filter((e) => e !== email);
      await assignUsersToManualTask({
        connectionKey,
        userIds: updated,
      }).unwrap();
      setSelectedUsers(updated);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Box>
      <Typography.Title level={5}>Assign tasks to users:</Typography.Title>

      <div className="mt-4 flex items-center justify-between gap-4">
        <div>
          <Button type="default" onClick={onManageSecureAccess}>
            Manage secure access
          </Button>
        </div>
        <div className="flex w-1/2 items-center justify-end gap-2">
          <Select
            className="!mt-0"
            placeholder="Select a user to assign"
            value={userToAssign}
            onChange={(val) => setUserToAssign(val)}
            options={availableUserOptions}
            style={{ width: "100%" }}
            filterOption={(input, option) =>
              (typeof option?.label === "string" &&
                option.label.toLowerCase().includes(input.toLowerCase())) ||
              false
            }
          />
          <Button type="primary" onClick={handleAssign} loading={isSaving}>
            Assign
          </Button>
        </div>
      </div>

      <div className="mt-4">
        <Table
          dataSource={(manualTaskConfig?.assigned_users || []).map(
            (u, idx) => ({
              key: u.email_address ?? idx,
              name: `${u.first_name ?? ""} ${u.last_name ?? ""}`.trim(),
              email: u.email_address ?? "",
              role: "—",
            }),
          )}
          pagination={false}
          size="small"
          columns={[
            { title: "Name", dataIndex: "name", key: "name" },
            { title: "Email", dataIndex: "email", key: "email" },
            {
              title: "Role",
              dataIndex: "role",
              key: "role",
              render: () => <span>—</span>,
            },
            {
              title: "Actions",
              key: "actions",
              width: 120,
              render: (_: any, record: any) => (
                <Flex gap={2}>
                  <Button
                    size="small"
                    danger
                    icon={<Icons.TrashCan />}
                    onClick={() => record.email && handleRemove(record.email)}
                  />
                </Flex>
              ),
            },
          ]}
          locale={{
            emptyText: (
              <div className="py-6 text-center">
                <Text color="gray.500">No users assigned.</Text>
              </div>
            ),
          }}
          bordered
        />
      </div>
    </Box>
  );
};

export default TaskAssignedUsersSection;
