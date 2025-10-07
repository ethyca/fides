import {
  AntButton as Button,
  AntFlex as Flex,
  AntInput as Input,
  AntList as List,
  AntPagination as Pagination,
  AntSpace as Space,
  AntTag as Tag,
  AntTypography as Typography,
} from "fidesui";
import { useRouter } from "next/router";

import { NOTIFICATIONS_ADD_DIGEST_ROUTE } from "~/features/common/nav/routes";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import { DIGEST_TYPE_LABELS, MESSAGING_METHOD_LABELS } from "../constants";
import { useDigestConfigList } from "../hooks/useDigestConfigList";

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
    canUpdate,
  } = useDigestConfigList();

  const canCreate = useHasPermission([ScopeRegistryEnum.DIGEST_CONFIG_CREATE]);

  const handleAddNew = () => {
    router.push(NOTIFICATIONS_ADD_DIGEST_ROUTE);
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
        renderItem={(config) => (
          <List.Item
            key={config.id}
            actions={
              canUpdate
                ? [
                    <Button
                      key="edit"
                      type="link"
                      onClick={() => handleEdit(config)}
                      data-testid="edit-list-btn"
                      className="px-1"
                    >
                      Edit
                    </Button>,
                  ]
                : []
            }
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
                  <Space size={4}>
                    <Tag>{DIGEST_TYPE_LABELS[config.digest_type]}</Tag>
                    <Tag>
                      {MESSAGING_METHOD_LABELS[config.messaging_service_type]}
                    </Tag>
                  </Space>
                </Space>
              }
            />
          </List.Item>
        )}
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
    </div>
  );
};

export default DigestConfigList;
