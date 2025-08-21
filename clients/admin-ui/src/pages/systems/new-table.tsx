/* eslint-disable react/no-unstable-nested-components */
import {
  AntButton,
  AntButton as Button,
  AntDropdown,
  AntFlex,
  AntMessage as message,
  AntModal,
  AntTable as Table,
  Icons,
} from "fidesui";
import { CustomTypography } from "fidesui/src/hoc";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import {
  expandCollapseAllMenuItems,
  MenuHeaderCell,
} from "~/features/common/table/cells/MenuHeaderCell";
import { formatKey } from "~/features/datastore-connections/system_portal_config/helpers";
import { useDeleteSystemMutation } from "~/features/system";
import CreateSystemGroupForm from "~/mocks/TEMP-system-groups/components/CreateSystemGroupForm";
import SystemDataUseCell from "~/mocks/TEMP-system-groups/components/SystemDataUseCell";
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
import { BasicSystemResponse, PrivacyDeclaration } from "~/types/api";

interface NewTableProps {
  data: BasicSystemResponse[];
  loading?: boolean;
}

const NewTable = ({ data, loading = false }: NewTableProps) => {
  const { data: allSystemGroups } = useMockGetSystemGroupsQuery();
  const [createSystemGroup] = useMockCreateSystemGroupMutation();
  const [deleteSystem] = useDeleteSystemMutation();
  const [bulkUpdate] = useMockBulkUpdateSystemWithGroupsMutation();

  const [messageApi, messageContext] = message.useMessage();

  const router = useRouter();

  const [createModalIsOpen, setCreateModalIsOpen] = useState(false);
  const [deleteModalIsOpen, setDeleteModalIsOpen] = useState(false);

  const [isGroupsExpanded, setIsGroupsExpanded] = useState(false);
  const [isDataUsesExpanded, setIsDataUsesExpanded] = useState(false);

  const [selectedSystemForDelete, setSelectedSystemForDelete] =
    useState<BasicSystemResponse | null>(null);

  const systemGroupMap = useMemo(() => {
    return allSystemGroups?.reduce(
      (acc, group) => ({
        ...acc,
        [group.fides_key]: group,
      }),
      {} as Record<string, SystemGroup>,
    );
  }, [allSystemGroups]);

  const handleDelete = async (system: BasicSystemResponse) => {
    const result = await deleteSystem(system.fides_key);
    if (isErrorResult(result)) {
      messageApi.error(
        getErrorMessage(result.error, "Failed to delete system"),
      );
    } else {
      messageApi.success("Successfully deleted system");
    }
    setDeleteModalIsOpen(false);
  };

  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  const rowSelection = {
    selectedRowKeys,
    onChange: setSelectedRowKeys,
  };

  const handleBulkAddToGroup = useCallback(
    async (groupKey: string) => {
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
    },
    [bulkUpdate, messageApi, selectedRowKeys],
  );

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
    setCreateModalIsOpen(false);
  };

  const columns = useMemo(() => {
    return [
      {
        title: "Name",
        dataIndex: "name",
        key: "name",
        render: (name: string | null, record: BasicSystemResponse) => (
          <LinkCell href={`/systems/${record.fides_key}`}>
            {name || record.fides_key}
          </LinkCell>
        ),
        width: 300,
        ellipsis: true,
      },
      {
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
            columnState={{
              isWrapped: true,
              isExpanded: isGroupsExpanded,
            }}
          />
        ),
        width: 400,
        title: () => (
          <MenuHeaderCell
            title="Groups"
            menu={{
              items: expandCollapseAllMenuItems,
              onClick: (e) => {
                e.domEvent.stopPropagation();
                if (e.key === "expand-all") {
                  setIsGroupsExpanded(true);
                } else if (e.key === "collapse-all") {
                  setIsGroupsExpanded(false);
                }
              },
            }}
          />
        ),
      },
      {
        title: () => (
          <MenuHeaderCell
            title="Data uses"
            menu={{
              items: expandCollapseAllMenuItems,
              onClick: (e) => {
                e.domEvent.stopPropagation();
                if (e.key === "expand-all") {
                  setIsDataUsesExpanded(true);
                } else if (e.key === "collapse-all") {
                  setIsDataUsesExpanded(false);
                }
              },
            }}
          />
        ),
        dataIndex: "privacy_declarations",
        key: "privacy_declarations",
        render: (privacyDeclarations: PrivacyDeclaration[]) => (
          <SystemDataUseCell
            privacyDeclarations={privacyDeclarations}
            columnState={{
              isWrapped: true,
              isExpanded: isDataUsesExpanded,
            }}
          />
        ),
        width: 500,
      },
      {
        title: "Data steward",
        dataIndex: "data_steward",
        key: "data_steward",
        render: (dataSteward: string | null) => dataSteward,
        width: 200,
      },
      {
        title: "Description",
        dataIndex: "description",
        key: "description",
        render: (description: string | null) => description,
        width: 200,
      },
      {
        title: "Actions",
        key: "actions",
        render: (_: unknown, record: BasicSystemResponse) => (
          <AntFlex justify="end">
            <AntDropdown
              trigger={["click"]}
              menu={{
                items: [
                  {
                    key: "edit",
                    label: "Edit",
                    icon: <Icons.Edit />,
                    onClick: () =>
                      router.push(`/systems/configure/${record.fides_key}`),
                  },
                  {
                    key: "delete",
                    label: "Delete",
                    icon: <Icons.TrashCan />,
                    onClick: () => {
                      setSelectedSystemForDelete(record);
                      setDeleteModalIsOpen(true);
                    },
                  },
                ],
              }}
            >
              <Button
                size="small"
                icon={<Icons.OverflowMenuVertical />}
                aria-label="More actions"
              />
            </AntDropdown>
          </AntFlex>
        ),
        width: 10,
      },
    ];
  }, [
    isGroupsExpanded,
    isDataUsesExpanded,
    systemGroupMap,
    allSystemGroups,
    router,
  ]);

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
                onClick: () => setCreateModalIsOpen(true),
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
        open={createModalIsOpen}
        destroyOnHidden
        onCancel={() => setCreateModalIsOpen(false)}
        centered
        width={768}
        footer={null}
      >
        <CreateSystemGroupForm
          selectedSystems={selectedRowKeys.map((key) => key.toString())}
          onSubmit={handleCreateSystemGroup}
          onCancel={() => setCreateModalIsOpen(false)}
        />
      </AntModal>
      <AntModal
        open={deleteModalIsOpen}
        onCancel={() => setDeleteModalIsOpen(false)}
        onOk={() => handleDelete(selectedSystemForDelete!)}
        okText="Delete"
        okType="danger"
        cancelText="Cancel"
        centered
      >
        <CustomTypography.Paragraph>
          Are you sure you want to delete{" "}
          {selectedSystemForDelete?.name ?? selectedSystemForDelete?.fides_key}?
          This action cannot be undone.
        </CustomTypography.Paragraph>
      </AntModal>
      <Table
        dataSource={data}
        columns={columns}
        loading={loading}
        rowKey="fides_key"
        size="small"
        rowSelection={rowSelection}
        tableLayout="fixed"
      />
    </>
  );
};

export default NewTable;
