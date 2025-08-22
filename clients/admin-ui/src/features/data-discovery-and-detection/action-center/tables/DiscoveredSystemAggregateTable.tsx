import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntFlex as Flex,
  AntMenu as Menu,
  AntSpace as Space,
  AntTable as Table,
  AntTooltip as Tooltip,
  Icons,
} from "fidesui";

import { SelectedText } from "~/features/common/table/SelectedText";
import { DiffStatus } from "~/types/api";

import { DebouncedSearchInput } from "../../../common/DebouncedSearchInput";
import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";
import { useDiscoveredSystemAggregateTable } from "../hooks/useDiscoveredSystemAggregateTable";

interface DiscoveredSystemAggregateTableProps {
  monitorId: string;
}

export const DiscoveredSystemAggregateTable = ({
  monitorId,
}: DiscoveredSystemAggregateTableProps) => {
  const {
    // Table state and data
    columns,
    searchQuery,
    updateSearch,

    // Ant Design table integration
    tableProps,
    selectionProps,

    // Tab management
    filterTabs,
    activeTab,
    handleTabChange,
    activeParams,

    // Selection
    selectedRows,
    hasSelectedRows,
    uncategorizedIsSelected,

    // Business actions
    handleBulkAdd,
    handleBulkIgnore,

    // Loading states
    anyBulkActionIsLoading,
  } = useDiscoveredSystemAggregateTable({ monitorId });

  return (
    <>
      <Menu
        aria-label="Asset state filter"
        mode="horizontal"
        items={filterTabs.map((tab) => ({
          key: tab.hash,
          label: tab.label,
        }))}
        selectedKeys={[activeTab]}
        onClick={async (menuInfo) => {
          await handleTabChange(menuInfo.key as ActionCenterTabHash);
        }}
        className="mb-4"
        data-testid="asset-state-filter"
      />
      <Flex justify="space-between" align="center" className="mb-4">
        <DebouncedSearchInput value={searchQuery} onChange={updateSearch} />
        <Space size="large">
          {hasSelectedRows && <SelectedText count={selectedRows.length} />}
          <Dropdown
            menu={{
              items: [
                {
                  key: "add",
                  label: (
                    <Tooltip
                      title={
                        uncategorizedIsSelected
                          ? "Uncategorized assets can't be added to the inventory"
                          : null
                      }
                      placement="left"
                    >
                      Add
                    </Tooltip>
                  ),
                  onClick: handleBulkAdd,
                  disabled: uncategorizedIsSelected,
                },
                !activeParams.diff_status.includes(DiffStatus.MUTED)
                  ? {
                      key: "ignore",
                      label: "Ignore",
                      onClick: handleBulkIgnore,
                    }
                  : null,
              ],
            }}
            trigger={["click"]}
          >
            <Button
              type="primary"
              icon={<Icons.ChevronDown />}
              iconPosition="end"
              loading={anyBulkActionIsLoading}
              disabled={!hasSelectedRows}
              data-testid="bulk-actions-menu"
            >
              Actions
            </Button>
          </Dropdown>
        </Space>
      </Flex>
      <Table {...tableProps} columns={columns} rowSelection={selectionProps} />
    </>
  );
};
