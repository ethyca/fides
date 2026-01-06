import {
  Button,
  DefaultOptionType,
  Dropdown,
  Empty,
  Flex,
  Icons,
  Menu,
  Space,
  Table,
  Tooltip,
} from "fidesui";
import { useState } from "react";

import { useFlags } from "~/features/common/features/features.slice";
import { SelectedText } from "~/features/common/table/SelectedText";
import {
  ConsentAlertInfo,
  DiffStatus,
  StagedResourceAPIResponse,
} from "~/types/api";

import { DebouncedSearchInput } from "../../../common/DebouncedSearchInput";
import AddDataUsesModal from "../AddDataUsesModal";
import { AssignSystemModal } from "../AssignSystemModal";
import { ClassificationReportModal } from "../ClassificationReportModal";
import { ConsentBreakdownModal } from "../ConsentBreakdownModal";
import { ActionCenterTabHash } from "../hooks/useActionCenterTabs";
import { useDiscoveredAssetsTable } from "../hooks/useDiscoveredAssetsTable";

interface DiscoveredAssetsTableProps {
  monitorId: string;
  systemId: string;
  consentStatus?: ConsentAlertInfo | null;
}

export const DiscoveredAssetsTable = ({
  monitorId,
  systemId,
  consentStatus,
}: DiscoveredAssetsTableProps) => {
  // Feature flags
  const { flags } = useFlags();
  const showLlmClassification = flags.alphaWebMonitorLlmClassification;

  // Modal state
  const [isAssignSystemModalOpen, setIsAssignSystemModalOpen] =
    useState<boolean>(false);
  const [isAddDataUseModalOpen, setIsAddDataUseModalOpen] =
    useState<boolean>(false);
  const [consentBreakdownModalData, setConsentBreakdownModalData] =
    useState<StagedResourceAPIResponse | null>(null);
  const [isClassificationReportOpen, setIsClassificationReportOpen] =
    useState<boolean>(false);

  const handleShowBreakdown = (stagedResource: StagedResourceAPIResponse) => {
    setConsentBreakdownModalData(stagedResource);
  };

  const handleCloseBreakdown = () => {
    setConsentBreakdownModalData(null);
  };

  const {
    // Table state and data
    columns,
    searchQuery,
    updateSearch,
    resetState,

    // Ant Design table integration
    tableProps,
    selectionProps,

    // Tab management
    filterTabs,
    activeTab,
    handleTabChange,
    activeParams,
    actionsDisabled,

    // Selection
    selectedUrns,
    hasSelectedRows,
    resetSelections,

    // Business actions
    handleBulkAdd,
    handleBulkAssignSystem,
    handleBulkAddDataUse,
    handleBulkIgnore,
    handleBulkRestore,
    handleAddAll,
    handleClassifyWithAI,

    // Loading states
    anyBulkActionIsLoading,
    isAddingAllResults,
    isBulkUpdatingSystem,
    isBulkAddingDataUses,
    isClassifyingAssets,
    disableAddAll,
  } = useDiscoveredAssetsTable({
    monitorId,
    systemId,
    consentStatus,
    onShowComplianceIssueDetails: handleShowBreakdown,
  });

  const handleClearFilters = () => {
    resetState();
    resetSelections();
  };

  const handleBulkAssignSystemWithModal = async (
    selectedSystem?: DefaultOptionType,
  ) => {
    await handleBulkAssignSystem(selectedSystem);
    setIsAssignSystemModalOpen(false);
  };

  const handleBulkAddDataUseWithModal = async (newDataUses: string[]) => {
    await handleBulkAddDataUse(newDataUses);
    setIsAddDataUseModalOpen(false);
  };

  if (!monitorId || !systemId) {
    return null;
  }

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
      <Flex
        justify="space-between"
        align="center"
        className="sticky -top-6 z-10 mb-4 bg-white py-4"
      >
        <DebouncedSearchInput
          value={searchQuery}
          onChange={updateSearch}
          placeholder="Search by asset name..."
        />
        <Space size="large">
          {hasSelectedRows && <SelectedText count={selectedUrns.length} />}
          <Space size="small">
            <Button onClick={handleClearFilters} data-testid="clear-filters">
              Clear filters
            </Button>
            <Dropdown
              overlayClassName="bulk-actions-menu-dropdown"
              menu={{
                items: [
                  ...(activeParams?.diff_status?.includes(DiffStatus.MUTED)
                    ? [
                        {
                          key: "restore",
                          label: "Restore",
                          onClick: handleBulkRestore,
                        },
                      ]
                    : [
                        {
                          key: "add",
                          label: "Add",
                          onClick: handleBulkAdd,
                        },
                        {
                          key: "add-data-use",
                          label: "Add consent category",
                          onClick: () => setIsAddDataUseModalOpen(true),
                        },
                        {
                          key: "assign-system",
                          label: "Assign system",
                          onClick: () => setIsAssignSystemModalOpen(true),
                        },
                        {
                          type: "divider" as const,
                        },
                        {
                          key: "ignore",
                          label: "Ignore",
                          onClick: handleBulkIgnore,
                        },
                        ...(showLlmClassification
                          ? [
                              {
                                type: "divider" as const,
                              },
                              {
                                key: "classify-ai",
                                label: "Classify with AI",
                                onClick: handleClassifyWithAI,
                              },
                            ]
                          : []),
                      ]),
                ],
              }}
              trigger={["click"]}
            >
              <Button
                icon={<Icons.ChevronDown />}
                iconPosition="end"
                loading={anyBulkActionIsLoading}
                data-testid="bulk-actions-menu"
                disabled={
                  !hasSelectedRows || anyBulkActionIsLoading || actionsDisabled
                }
                type="primary"
              >
                Actions
              </Button>
            </Dropdown>

            {showLlmClassification && (
              <>
                <Button
                  onClick={handleClassifyWithAI}
                  loading={isClassifyingAssets}
                  disabled={anyBulkActionIsLoading || actionsDisabled}
                  data-testid="classify-ai"
                >
                  Classify with AI
                </Button>
                <Button
                  onClick={() => setIsClassificationReportOpen(true)}
                  data-testid="classification-report"
                >
                  Report
                </Button>
              </>
            )}
            <Tooltip
              title={
                disableAddAll
                  ? `These assets require a system before you can add them to the inventory.`
                  : undefined
              }
            >
              <Button
                onClick={handleAddAll}
                disabled={disableAddAll}
                loading={isAddingAllResults}
                type="primary"
                icon={<Icons.Checkmark />}
                iconPosition="end"
                data-testid="add-all"
              >
                Add all
              </Button>
            </Tooltip>
          </Space>
        </Space>
      </Flex>
      <Table
        {...tableProps}
        columns={columns}
        rowSelection={selectionProps}
        locale={{
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="All caught up!"
            />
          ),
        }}
        aria-labelledby="breadcrumb-current-page"
      />
      <AssignSystemModal
        isOpen={isAssignSystemModalOpen}
        onClose={() => {
          setIsAssignSystemModalOpen(false);
        }}
        onSave={handleBulkAssignSystemWithModal}
        isSaving={isBulkUpdatingSystem}
      />
      <AddDataUsesModal
        isOpen={isAddDataUseModalOpen}
        onClose={() => {
          setIsAddDataUseModalOpen(false);
        }}
        onSave={handleBulkAddDataUseWithModal}
        isSaving={isBulkAddingDataUses}
      />
      {consentBreakdownModalData && (
        <ConsentBreakdownModal
          isOpen={!!consentBreakdownModalData}
          stagedResource={consentBreakdownModalData}
          onCancel={handleCloseBreakdown}
        />
      )}
      {showLlmClassification && (
        <ClassificationReportModal
          monitorId={monitorId}
          open={isClassificationReportOpen}
          onClose={() => setIsClassificationReportOpen(false)}
        />
      )}
    </>
  );
};

export default DiscoveredAssetsTable;
