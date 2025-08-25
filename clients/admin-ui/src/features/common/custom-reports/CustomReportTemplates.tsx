import {
  AntButton as Button,
  AntEmpty as Empty,
  AntFlex as Flex,
  AntInput as Input,
  AntPopover as Popover,
  AntRadio as Radio,
  AntSkeleton as Skeleton,
  AntSpace as Space,
  AntText as Text,
  ChevronDownIcon,
  ConfirmationModal,
  Icons,
  useDisclosure,
  useToast,
} from "fidesui";
import { Form, Formik, FormikState, useFormikContext } from "formik";
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
  onCustomReportSaved: (
    customReport: CustomReportResponse | null,
    resetForm: (
      nextState?: Partial<FormikState<Record<string, string>>> | undefined,
    ) => void,
  ) => void;
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

  const toast = useToast({ id: "custom-report-toast" });

  const { data: customReportsList, isLoading: isCustomReportsLoading } =
    useGetMinimalCustomReportsQuery({ report_type: reportType });
  const [searchResults, setSearchResults] =
    useState<Page_CustomReportResponseMinimal_["items"]>();
  const [getCustomReportByIdTrigger] = useLazyGetCustomReportByIdQuery();
  const [deleteCustomReportMutationTrigger] = useDeleteCustomReportMutation();
  const {
    isOpen: popoverIsOpen,
    onOpen: popoverOnOpen,
    onClose: popoverOnClose,
  } = useDisclosure();
  const {
    isOpen: modalIsOpen,
    onOpen: modalOnOpen,
    onClose: modalOnClose,
  } = useDisclosure();
  const {
    isOpen: deleteIsOpen,
    onOpen: onDeleteOpen,
    onClose: onDeleteClose,
  } = useDisclosure();

  const [selectedReportId, setSelectedReportId] = useState<string>(); // for the radio buttons
  const [fetchedReport, setFetchedReport] = useState<CustomReportResponse>();
  const [reportToDelete, setReportToDelete] =
    useState<CustomReportResponseMinimal>();
  const [showSpinner, setShowSpinner] = useState<boolean>(false);
  const { resetForm } = useFormikContext();

  const buttonLabel = useMemo(() => {
    const reportName = customReportsList?.items.find(
      (report) => report.id === savedReportId,
    )?.name;
    return reportName ?? CUSTOM_REPORTS_TITLE;
  }, [customReportsList?.items, savedReportId]);

  const isEmpty = !isCustomReportsLoading && !customReportsList?.items?.length;

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
      toast({ status: "error", description: errorMsg });
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
    popoverOnClose();
  };

  const handleApplyTemplate = () => {
    if (fetchedReport) {
      setShowSpinner(false);
      if (fetchedReport.id !== savedReportId) {
        onCustomReportSaved(fetchedReport, resetForm);
      }
      popoverOnClose();
    } else if (selectedReportId) {
      // user clicked apply before the report was fetched
      setShowSpinner(true);
    } else {
      // form was reset, apply the reset
      onCustomReportSaved(null, resetForm);
      popoverOnClose();
    }
  };

  const handleDeleteReport = async (id: string) => {
    if (id === fetchedReport?.id) {
      handleReset();
      onSavedReportDeleted();
    }
    deleteCustomReportMutationTrigger(id);
  };

  const handleCloseModal = () => {
    modalOnClose();
    setTimeout(() => {
      // switch back to the popover once the modal has closed
      popoverOnOpen();
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

  useEffect(() => {
    if (reportToDelete) {
      onDeleteOpen();
    }
  }, [onDeleteOpen, reportToDelete]);

  const applyDisabled =
    (!fetchedReport && !savedReportId) || fetchedReport?.id === savedReportId;

  const popoverContent = (
    <div data-testid="custom-reports-popover">
      <Formik
        initialValues={{}}
        onSubmit={handleApplyTemplate}
        onReset={handleReset}
      >
        <Form>
          <div
            className="relative p-3"
            style={{
              borderBottom: "var(--ant-popover-title-border-bottom)",
            }}
          >
            <Button
              size="small"
              disabled={isEmpty}
              htmlType="reset"
              className="absolute left-3 top-3"
              data-testid="custom-reports-reset-button"
            >
              Reset
            </Button>
            <Button
              type="text"
              size="small"
              icon={<Icons.Close />}
              className="absolute right-3 top-3"
              onClick={handleCancel}
              data-testid="custom-report-popover-cancel"
            />
            <div
              className="text-center"
              style={{
                color: "var(--ant-color-text-heading)",
                fontWeight: "var(--ant-font-weight-strong)",
              }}
            >
              {CUSTOM_REPORTS_TITLE}
            </div>
            <div className="mt-3">
              <Input
                size="small"
                placeholder="Search..."
                onChange={(e) => handleSearch(e.target.value)}
              />
            </div>
          </div>

          <div className="px-5 pb-1 pt-3">
            {isEmpty && (
              <Empty
                image={
                  <Button
                    type="primary"
                    shape="circle"
                    size="small"
                    aria-label={`add ${CUSTOM_REPORT_TITLE}`}
                    icon={<Icons.Add />}
                    onClick={modalOnOpen}
                    data-testid="add-report-button"
                  />
                }
                description={`No ${CUSTOM_REPORTS_TITLE.toLowerCase()} have been created. Start by applying your preferred filter and column settings, then create a ${CUSTOM_REPORT_TITLE.toLowerCase()} for easy access later.`}
                styles={{
                  image: {
                    height: "24px",
                  },
                }}
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
                  <Space direction="vertical" className="w-full" size="small">
                    {searchResults?.map((customReport) => (
                      <Flex
                        key={customReport.id}
                        justify={
                          userCanDeleteReports ? "space-between" : "flex-start"
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
                            onClick={() => setReportToDelete(customReport)}
                            data-testid="delete-report-button"
                          />
                        )}
                      </Flex>
                    ))}
                  </Space>
                </Radio.Group>
              ))}
          </div>

          <Flex className="px-5 py-4" gap="small">
            {userCanCreateReports && tableStateToSave && (
              <Button
                size="small"
                onClick={modalOnOpen}
                className="flex-1 gap-1 pl-0"
                data-testid="create-report-button"
                htmlType="button"
                icon={<Icons.Add />}
                iconPosition="start"
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
        </Form>
      </Formik>
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
            popoverOnOpen();
          } else {
            handleApplyTemplate();
          }
        }}
        styles={{
          root: {
            width: "320px",
            // @ts-expect-error setting a custom css variable
            "--ant-popover-inner-content-padding": "0",
          },
        }}
        zIndex={1400} // below chakra modals
      >
        <Button
          className="max-w-40"
          icon={<ChevronDownIcon />}
          iconPosition="end"
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
          onCustomReportSaved(customReport, resetForm)
        }
      />
      <ConfirmationModal
        isOpen={deleteIsOpen}
        onClose={() => {
          setReportToDelete(undefined);
          onDeleteClose();
        }}
        onConfirm={() => {
          if (reportToDelete) {
            handleDeleteReport(reportToDelete.id);
          }
          onDeleteClose();
        }}
        title={`Delete ${CUSTOM_REPORT_TITLE}`}
        message={
          <Text>
            You are about to permanently delete the{" "}
            {CUSTOM_REPORT_TITLE.toLowerCase()} named{" "}
            <strong>{reportToDelete?.name}</strong>. Are you sure you would like
            to continue?
          </Text>
        }
      />
    </>
  );
};
