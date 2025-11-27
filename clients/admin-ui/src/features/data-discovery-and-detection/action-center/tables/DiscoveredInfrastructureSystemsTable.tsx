import {
  AntFlex as Flex,
  AntMenu as Menu,
  AntSpace as Space,
  AntTable as Table,
} from "fidesui";

import { SelectedText } from "~/features/common/table/SelectedText";

import { DebouncedSearchInput } from "../../../common/DebouncedSearchInput";
import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";
import { useDiscoveredInfrastructureSystemsTable } from "../hooks/useDiscoveredInfrastructureSystemsTable";

interface DiscoveredInfrastructureSystemsTableProps {
  monitorId: string;
}

export const DiscoveredInfrastructureSystemsTable = ({
  monitorId,
}: DiscoveredInfrastructureSystemsTableProps) => {
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

    // Selection
    selectedRows,
    hasSelectedRows,
  } = useDiscoveredInfrastructureSystemsTable({ monitorId });

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
          await handleTabChange(menuInfo.key as string | ActionCenterTabHash);
        }}
        className="mb-4"
        data-testid="asset-state-filter"
      />
      <Flex justify="space-between" align="center" className="mb-4">
        <DebouncedSearchInput value={searchQuery} onChange={updateSearch} />
        <Space size="large">
          {hasSelectedRows && <SelectedText count={selectedRows.length} />}
        </Space>
      </Flex>
      <Table {...tableProps} columns={columns} rowSelection={selectionProps} />
    </>
  );
};
