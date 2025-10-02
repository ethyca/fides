import {
  AntButton as Button,
  AntFlex as Flex,
  AntInput as Input,
  AntList as List,
  AntPagination as Pagination,
  AntSpace as Space,
  AntTag as Tag,
  AntTypography as Typography,
  WarningIcon,
} from "fidesui";
import { useRouter } from "next/router";

import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import { useDigestConfigList } from "../hooks/useDigestConfigList";

const { Text } = Typography;
const { Search } = Input;

const DigestConfigList = () => {
  const router = useRouter();
  const {
    data,
    total,
    isLoading,
    page,
    pageSize,
    searchQuery,
    setPage,
    setPageSize,
    setSearchQuery,
    handleEdit,
    handleDeleteClick,
    deleteModalOpen,
    configToDelete,
    confirmDelete,
    cancelDelete,
    canUpdate,
    canDelete,
  } = useDigestConfigList();

  const canCreate = useHasPermission([ScopeRegistryEnum.DIGEST_CONFIG_CREATE]);

  const handleAddNew = () => {
    router.push("/settings/digests/new");
  };

  return (
    <div>
      {/* Header with search and add button */}
      <Flex justify="space-between" align="center" className="mb-4">
        <Search
          placeholder="Search digests..."
          allowClear
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ width: 300 }}
          data-testid="search-input"
        />
        {canCreate && (
          <Button
            type="primary"
            onClick={handleAddNew}
            data-testid="add-digest-btn"
          >
            Create digest
          </Button>
        )}
      </Flex>

      {/* List */}
      <List
        loading={isLoading}
        itemLayout="horizontal"
        dataSource={data}
        locale={{
          emptyText: (
            <div className="px-4 py-8 text-center">
              <Typography.Paragraph type="secondary">
                No digest configurations yet. <br />
                Click &quot;Create digest&quot; to get started.
              </Typography.Paragraph>
            </div>
          ),
        }}
        renderItem={(config) => {
          const scheduleText = `${config.cron_expression} (${config.timezone})`;
          const lastSent = config.last_sent_at
            ? new Date(config.last_sent_at).toLocaleDateString()
            : "Never";

          return (
            <List.Item
              key={config.id}
              actions={[
                canUpdate && (
                  <Button
                    key="edit"
                    type="link"
                    onClick={() => handleEdit(config)}
                    data-testid="edit-list-btn"
                    className="px-1"
                  >
                    Edit
                  </Button>
                ),
                canDelete && (
                  <Button
                    key="delete"
                    type="link"
                    onClick={() => handleDeleteClick(config)}
                    data-testid="delete-list-btn"
                    className="px-1"
                  >
                    Delete
                  </Button>
                ),
              ].filter(Boolean)}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <span>{config.name}</span>
                    {!config.enabled && <Tag color="default">Inactive</Tag>}
                  </Space>
                }
                description={
                  <Space direction="vertical" size={4}>
                    {config.description && (
                      <Text type="secondary">{config.description}</Text>
                    )}
                    <Text type="secondary" className="text-xs">
                      Schedule: {scheduleText} • Last sent: {lastSent}
                    </Text>
                  </Space>
                }
              />
            </List.Item>
          );
        }}
      />

      {/* Pagination */}
      {total > pageSize && (
        <Flex justify="end" className="mt-4">
          <Pagination
            current={page}
            total={total}
            pageSize={pageSize}
            onChange={(newPage, newPageSize) => {
              setPage(newPage);
              if (newPageSize !== pageSize) {
                setPageSize(newPageSize);
              }
            }}
            showSizeChanger
            showTotal={(totalItems) => `Total ${totalItems} items`}
          />
        </Flex>
      )}

      {/* Delete Confirmation Modal */}
      <ConfirmationModal
        isOpen={deleteModalOpen}
        onClose={cancelDelete}
        onConfirm={confirmDelete}
        title="Delete digest configuration"
        message={
          <span className="text-gray-500">
            Are you sure you want to delete the digest &quot;
            {configToDelete?.name}&quot;? This action cannot be undone.
          </span>
        }
        continueButtonText="Delete"
        isCentered
        icon={<WarningIcon />}
      />
    </div>
  );
};

export default DigestConfigList;
