import {
  Button,
  Empty,
  Flex,
  Form,
  Icons,
  Input,
  Popover,
  Radio,
  Skeleton,
  Space,
  Tag,
  Text,
  Title,
  Tooltip,
  useMessage,
  useModal,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { useHasPermission } from "~/features/common/Restrict";
import {
  CustomReportResponse,
  CustomReportResponseMinimal,
  Page_CustomReportResponseMinimal_,
  ReportType,
  ScopeRegistryEnum,
} from "~/types/api";

import {
  useDeleteCustomReportMutation,
  useGetMinimalCustomReportsQuery,
  useLazyGetCustomReportByIdQuery,
} from "../../datamap/reporting/custom-reports.slice";
import { CustomReportTableState } from "../../datamap/types";
import { CustomReportCreationModal } from "./CustomReportCreationModal";

const CUSTOM_REPORT_TITLE = "Report";
const CUSTOM_REPORTS_TITLE = "Reports";

interface CustomReportTemplatesProps {
  reportType: ReportType;
  savedReportId: string; // from local storage
  tableStateToSave: CustomReportTableState | undefined;
  currentColumnMap?: Record<string, string>;
  onCustomReportSaved: (customReport: CustomReportResponse | null) => void;
  onSavedReportDeleted: () => void;
}

export const CustomReportTemplates = ({
  reportType,
  savedReportId,
  tableStateToSave,
  currentColumnMap,
  onCustomReportSaved,
  onSavedReportDeleted,
}: CustomReportTemplatesProps) => {
  const userCanCreateReports = useHasPermission([
    ScopeRegistryEnum.CUSTOM_REPORT_CREATE,
  ]);
  const userCanDeleteReports = useHasPermission([
    ScopeRegistryEnum.CUSTOM_REPORT_DELETE,
  ]);

  const message = useMessage();

  const { data: customReportsList, isLoading: isCustomReportsLoading } =
    useGetMinimalCustomReportsQuery({ report_type: reportType });
  const [searchResults, setSearchResults] =
    useState<Page_CustomReportResponseMinimal_["items"]>();
  const [getCustomReportByIdTrigger] = useLazyGetCustomReportByIdQuery();
  const [deleteCustomReportMutationTrigger] = useDeleteCustomReportMutation();

  const [popoverIsOpen, setPopoverIsOpen] = useState(false);
  const [modalIsOpen, setModalIsOpen] = useState(false);
  const confirmModal = useModal();

  const [selectedReportId, setSelectedReportId] = useState<string>(); // for the radio buttons
  const [fetchedReport, setFetchedReport] = useState<CustomReportResponse>();
  const [showSpinner, setShowSpinner] = useState<boolean>(false);

  const buttonLabel = useMemo(() => {
    const reportName = customReportsList?.items.find(
      (report) => report.id === savedReportId,
    )?.name;
    return reportName ?? CUSTOM_REPORTS_TITLE;
  }, [customReportsList?.items, savedReportId]);

  const isEmpty = !isCustomReportsLoading && !customReportsList?.items?.length;

  const { systemReports, userReports } = useMemo(() => {
    const items = searchResults ?? [];
    return {
      systemReports: items.filter((report) => !!report.system_template_key),
      userReports: items.filter((report) => !report.system_template_key),
    };
  }, [searchResults]);

  const handleSearch = (searchTerm: string) => {
    const results = customReportsList?.items.filter((customReport) =>
      customReport.name.toLowerCase().includes(searchTerm.toLowerCase()),
    );
    setSearchResults(results);
  };

  const handleSelection = async (id: string) => {
    setSelectedReportId(id);
    const { data, isError, error } = await getCustomReportByIdTrigger(id);
    if (isError) {
      const errorMsg = getErrorMessage(
        error,
        `A problem occurred while fetching the ${CUSTOM_REPORT_TITLE}.`,
      );
      if (errorMsg.includes("not found")) {
        onSavedReportDeleted();
      }
      message.error(errorMsg);
    } else {
      setFetchedReport(data);
    }
  };

  const handleReset = () => {
    setSelectedReportId("");
    setFetchedReport(undefined);
    setShowSpinner(false);
  };

  const handleCancel = () => {
    if (savedReportId) {
      handleSelection(savedReportId);
    } else {
      handleReset();
    }
    setPopoverIsOpen(false);
  };

  const handleApplyTemplate = () => {
    if (fetchedReport) {
      setShowSpinner(false);
      if (fetchedReport.id !== savedReportId) {
        onCustomReportSaved(fetchedReport);
      }
      setPopoverIsOpen(false);
    } else if (selectedReportId) {
      // user clicked apply before the report was fetched
      setShowSpinner(true);
    } else {
      // form was reset, apply the reset
      onCustomReportSaved(null);
      setPopoverIsOpen(false);
    }
  };

  const handleDeleteReport = async (id: string) => {
    if (id === fetchedReport?.id) {
      handleReset();
      onSavedReportDeleted();
    }
    deleteCustomReportMutationTrigger(id);
  };

  const onDelete = (report: CustomReportResponseMinimal) => {
    confirmModal.confirm({
      title: `Delete ${CUSTOM_REPORT_TITLE}`,
      content: (
        <>
          You are about to permanently delete the{" "}
          {CUSTOM_REPORT_TITLE.toLowerCase()} named{" "}
          <strong>{report.name}</strong>. Are you sure you would like to
          continue?
        </>
      ),
      okButtonProps: { danger: true },
      onOk: () => handleDeleteReport(report.id),
    });
  };

  const handleCloseModal = () => {
    setModalIsOpen(false);
    setTimeout(() => {
      // switch back to the popover once the modal has closed
      setPopoverIsOpen(true);
    }, 100);
  };

  useEffect(() => {
    if (customReportsList) {
      setSearchResults(customReportsList.items);
    }
  }, [customReportsList]);

  useEffect(() => {
    // If the user clicks the apply button before the report is fetched, the spinner will show. Once the selected report is fetched, stop the spinner and apply the template.
    if (showSpinner) {
      setShowSpinner(false);
      handleApplyTemplate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchedReport]);

  useEffect(() => {
    // When we first load the component, we want to get and apply the saved report id from local storage.
    if (savedReportId) {
      handleSelection(savedReportId);
    } else {
      handleReset();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [savedReportId]);

  const applyDisabled =
    (!fetchedReport && !savedReportId) || fetchedReport?.id === savedReportId;

  const popoverContent = (
    <div data-testid="custom-reports-popover">
      <Form onFinish={handleApplyTemplate}>
        <Flex vertical gap="medium">
          <div className="relative">
            {!isEmpty && (
              <Button
                size="small"
                disabled={isEmpty}
                onClick={handleReset}
                className="absolute left-0 top-0"
                data-testid="custom-reports-reset-button"
              >
                Reset
              </Button>
            )}
            <Button
              type="text"
              size="small"
              aria-label="Cancel"
              icon={<Icons.Close />}
              className="absolute right-0 top-0"
              onClick={handleCancel}
              data-testid="custom-report-popover-cancel"
            />
            <Title level={5} className="text-center">
              {CUSTOM_REPORTS_TITLE}
            </Title>
            {!isEmpty && (
              <Input
                size="small"
                placeholder="Search..."
                aria-label="Search"
                onChange={(e) => handleSearch(e.target.value)}
                className="mt-3"
              />
            )}
          </div>
          {isEmpty && (
            <Empty
              image={
                <Button
                  type="primary"
                  shape="circle"
                  size="small"
                  aria-label={`add ${CUSTOM_REPORT_TITLE}`}
                  icon={<Icons.Add />}
                  onClick={() => setModalIsOpen(true)}
                  data-testid="add-report-button"
                />
              }
              description={`No ${CUSTOM_REPORTS_TITLE.toLowerCase()} have been created. Start by applying your preferred filter and column settings, then create a ${CUSTOM_REPORT_TITLE.toLowerCase()} for easy access later.`}
              styles={{
                image: {
                  height: "24px",
                },
              }}
              data-testid="custom-reports-empty-state"
            />
          )}
          {!isEmpty &&
            (isCustomReportsLoading ? (
              <Skeleton
                active
                paragraph={{ rows: 3, width: "100%" }}
                title={false}
                className="pt-2"
              />
            ) : (
              <Radio.Group
                onChange={(e) => handleSelection(e.target.value)}
                value={selectedReportId}
                style={{ width: "100%" }}
              >
                <Space orientation="vertical" className="w-full" size="small">
                  {systemReports.length > 0 && (
                    <>
                      <Text
                        type="secondary"
                        className="text-xs uppercase tracking-wide"
                        data-testid="custom-reports-section-system"
                      >
                        Standard templates
                      </Text>
                      {systemReports.map((customReport) => (
                        <Flex
                          key={customReport.id}
                          justify="flex-start"
                          align="center"
                          gap="small"
                        >
                          <Radio
                            value={customReport.id}
                            name="custom-report-id"
                            data-testid="custom-report-item"
                          >
                            {customReport.name}
                          </Radio>
                          <Tooltip title="Out-of-the-box reporting template. Standard templates cannot be deleted.">
                            <Tag
                              color="info"
                              className="m-0"
                              data-testid="system-template-tag"
                            >
                              Standard
                            </Tag>
                          </Tooltip>
                        </Flex>
                      ))}
                    </>
                  )}
                  {userReports.length > 0 && (
                    <>
                      {systemReports.length > 0 && (
                        <Text
                          type="secondary"
                          className="mt-2 text-xs uppercase tracking-wide"
                          data-testid="custom-reports-section-user"
                        >
                          Your reports
                        </Text>
                      )}
                      {userReports.map((customReport) => (
                        <Flex
                          key={customReport.id}
                          justify={
                            userCanDeleteReports
                              ? "space-between"
                              : "flex-start"
                          }
                          align="center"
                        >
                          <Radio
                            value={customReport.id}
                            name="custom-report-id"
                            data-testid="custom-report-item"
                          >
                            {customReport.name}
                          </Radio>
                          {userCanDeleteReports && (
                            <Button
                              type="text"
                              size="small"
                              icon={<Icons.TrashCan />}
                              onClick={() => onDelete(customReport)}
                              data-testid="delete-report-button"
                              aria-label="Delete"
                            />
                          )}
                        </Flex>
                      ))}
                    </>
                  )}
                </Space>
              </Radio.Group>
            ))}
          <Flex gap="small">
            {userCanCreateReports && tableStateToSave && (
              <Button
                size="small"
                onClick={() => setModalIsOpen(true)}
                className="flex-1 gap-1 pl-0"
                data-testid="create-report-button"
                htmlType="button"
                icon={<Icons.Add />}
                iconPlacement="start"
              >
                Create {CUSTOM_REPORT_TITLE.toLowerCase()}
              </Button>
            )}
            <Button
              size="small"
              type="primary"
              loading={showSpinner}
              disabled={applyDisabled}
              className="flex-1"
              data-testid="apply-report-button"
              htmlType="submit"
            >
              Apply
            </Button>
          </Flex>
        </Flex>
      </Form>
    </div>
  );

  return (
    <>
      <Popover
        content={popoverContent}
        trigger="click"
        placement="bottomRight"
        open={popoverIsOpen}
        onOpenChange={(open) => {
          if (open) {
            setPopoverIsOpen(true);
          } else {
            handleApplyTemplate();
          }
        }}
        styles={{
          root: {
            width: "320px",
          },
        }}
        zIndex={1400} // below chakra modals
      >
        <Button
          className="max-w-40"
          icon={<Icons.ChevronDown size={14} />}
          iconPlacement="end"
          data-testid="custom-reports-trigger"
        >
          <Text ellipsis>{buttonLabel}</Text>
        </Button>
      </Popover>
      <CustomReportCreationModal
        isOpen={modalIsOpen}
        handleClose={handleCloseModal}
        tableStateToSave={tableStateToSave}
        columnMapToSave={currentColumnMap}
        unavailableNames={customReportsList?.items.map((customReport) => {
          return customReport.name;
        })}
        onCreateCustomReport={(customReport) =>
          onCustomReportSaved(customReport)
        }
      />
    </>
  );
};
