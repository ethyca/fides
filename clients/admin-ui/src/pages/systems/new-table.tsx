import type { ColumnsType } from "antd/es/table/interface";
import {
  AntButton,
  AntButton as Button,
  AntDropdown,
  AntFlex,
  AntMessage as message,
  AntModal,
  AntSpace as Space,
  AntTable as Table,
  Icons,
} from "fidesui";
import { useMemo, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import CreateSystemGroupForm from "~/mocks/TEMP-system-groups/components/CreateSystemGroupForm";
import SystemGroupCell from "~/mocks/TEMP-system-groups/components/SystemGroupCell";
import {
  useMockCreateSystemGroupMutation,
  useMockGetSystemGroupsQuery,
} from "~/mocks/TEMP-system-groups/endpoints/system-groups";
import { useMockBulkUpdateSystemWithGroupsMutation } from "~/mocks/TEMP-system-groups/endpoints/systems";
import {
  SystemGroup,
  SystemGroupCreate,
} from "~/mocks/TEMP-system-groups/types";
import { BasicSystemResponse } from "~/types/api";

interface NewTableProps {
  data: BasicSystemResponse[];
  loading?: boolean;
}

const NewTable = ({ data, loading = false }: NewTableProps) => {
  const { data: allSystemGroups } = useMockGetSystemGroupsQuery();
  const [createSystemGroup] = useMockCreateSystemGroupMutation();

  const [messageApi, messageContext] = message.useMessage();

  const [createModalOpen, setCreateModalOpen] = useState(false);

  const systemGroupMap = useMemo(() => {
    return allSystemGroups?.reduce(
      (acc, group) => ({
        ...acc,
        [group.fides_key]: group,
      }),
      {} as Record<string, SystemGroup>,
    );
  }, [allSystemGroups]);

  const [bulkUpdate] = useMockBulkUpdateSystemWithGroupsMutation();
  const handleEdit = (record: BasicSystemResponse) => {
    console.log("Edit clicked for system:", record.fides_key);
  };

  const handleDelete = (record: BasicSystemResponse) => {
    console.log("Delete clicked for system:", record.fides_key);
  };

  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
  };

  const handleBulkAddToGroup = async (groupKey: string) => {
    const result = await bulkUpdate({
      system_keys: selectedRowKeys.map((key) => key.toString()),
      group_key: groupKey,
    });
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success(
        `${selectedRowKeys.length} systems added to group '${groupKey}'`,
      );
    }
  };

  const handleCreateSystemGroup = async (systemGroup: SystemGroupCreate) => {
    const payload = {
      ...systemGroup,
      // TODO: add input for handling fides_key
      fides_key: formatKey(systemGroup.name),
    };
    const result = await createSystemGroup(payload);
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
    } else {
      messageApi.success(
        `System group '${result.data.name}' created with ${result.data.systems.length} systems`,
      );
    }
    setCreateModalOpen(false);
  };

  const columns: ColumnsType<BasicSystemResponse> = [
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      render: (name: string | null, record: BasicSystemResponse) => (
        <LinkCell href={`/systems/${record.fides_key}`}>
          {name || record.fides_key}
        </LinkCell>
      ),
    },
    {
      title: "Description",
      dataIndex: "description",
      key: "description",
      render: (description: string | null) => description,
    },
    {
      title: "Groups",
      dataIndex: "groups",
      key: "groups",
      render: (groups: string[], record: BasicSystemResponse) => (
        <SystemGroupCell
          // @ts-ignore - TS doesn't know we filter out undefineds
          selectedGroups={groups
            .map((key) => systemGroupMap?.[key])
            .filter((group) => group !== undefined)}
          allGroups={allSystemGroups!}
          system={{ ...record, groups }}
        />
      ),
    },
    {
      title: "Department",
      dataIndex: "administrating_department",
      key: "administrating_department",
      render: (department: string | null) => department,
    },
    {
      title: "Processes personal data",
      dataIndex: "processes_personal_data",
      key: "processes_personal_data",
      render: (processesPersonalData: boolean | null) =>
        processesPersonalData ? "Yes" : "No",
    },
    {
      title: "Actions",
      key: "actions",
      render: (_, record: BasicSystemResponse) => (
        <Space size="small">
          <Button
            size="small"
            icon={<Icons.Edit />}
            onClick={() => handleEdit(record)}
            aria-label="Edit"
          />
          <Button
            size="small"
            icon={<Icons.TrashCan />}
            onClick={() => handleDelete(record)}
            aria-label="Delete"
          />
        </Space>
      ),
    },
  ];

  const groupMenuItems = useMemo(() => {
    return (
      allSystemGroups?.map((group) => ({
        key: group.fides_key,
        label: group.name,
        onClick: () => handleBulkAddToGroup(group.fides_key),
      })) ?? []
    );
  }, [allSystemGroups, handleBulkAddToGroup]);

  return (
    <>
      {messageContext}
      <AntFlex justify="end">
        <AntDropdown
          trigger={["click"]}
          menu={{
            items: [
              {
                key: "new-group",
                label: "Create new group +",
                onClick: () => setCreateModalOpen(true),
              },
              {
                type: "divider",
              },
              ...groupMenuItems,
            ],
          }}
          className="my-4"
        >
          <AntButton
            disabled={selectedRowKeys.length === 0}
            icon={<Icons.ChevronDown />}
          >
            Add to group
          </AntButton>
        </AntDropdown>
      </AntFlex>
      <AntModal
        open={createModalOpen}
        destroyOnHidden
        onCancel={() => setCreateModalOpen(false)}
        centered
        width={768}
        footer={null}
      >
        <CreateSystemGroupForm
          selectedSystems={selectedRowKeys.map((key) => key.toString())}
          onSubmit={handleCreateSystemGroup}
          onCancel={() => setCreateModalOpen(false)}
        />
      </AntModal>
      <Table
        dataSource={data}
        columns={columns}
        loading={loading}
        rowKey="fides_key"
        size="small"
        rowSelection={rowSelection}
      />
    </>
  );
};

export default NewTable;
