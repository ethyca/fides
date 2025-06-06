import {
  AntButton as Button,
  AntFlex as Flex,
  AntRadio as Radio,
  ChevronDownIcon,
  ConfirmationModal,
  HStack,
  Input,
  InputGroup,
  Popover,
  PopoverArrow,
  PopoverBody,
  PopoverCloseButton,
  PopoverContent,
  PopoverFooter,
  PopoverHeader,
  PopoverTrigger,
  Portal,
  Skeleton,
  Text,
  theme,
  useDisclosure,
  useToast,
  VStack,
} from "fidesui";
import { Form, Formik, FormikState, useFormikContext } from "formik";
import { useEffect, useMemo, useState } from "react";

import { AddIcon } from "~/features/common/custom-fields/icons/AddIcon";
import { getErrorMessage } from "~/features/common/helpers";
import { TrashCanOutlineIcon } from "~/features/common/Icon/TrashCanOutlineIcon";
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
    onToggle: popoverOnToggle,
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

  return (
    <>
      <Popover
        placement="bottom-end"
        isOpen={popoverIsOpen}
        onClose={handleApplyTemplate}
        id="custom-reports-selection"
      >
        <PopoverTrigger>
          <Button
            className="max-w-40"
            icon={<ChevronDownIcon />}
            iconPosition="end"
            data-testid="custom-reports-trigger"
            onClick={popoverOnToggle}
          >
            <Text noOfLines={1} display="inline-block">
              {buttonLabel}
            </Text>
          </Button>
        </PopoverTrigger>
        <Portal>
          <PopoverContent data-testid="custom-reports-popover">
            <PopoverArrow />
            <Formik
              initialValues={{}}
              onSubmit={handleApplyTemplate}
              onReset={handleReset}
            >
              <Form>
                <Button
                  size="small"
                  disabled={isEmpty}
                  htmlType="reset"
                  className="absolute left-2 top-2"
                  data-testid="custom-reports-reset-button"
                >
                  Reset
                </Button>
                <PopoverHeader textAlign="center">
                  <Text fontSize="sm">{CUSTOM_REPORTS_TITLE}</Text>
                  <InputGroup size="sm" mt={3}>
                    <Input
                      type="text"
                      borderRadius="md"
                      placeholder="Search..."
                      onChange={(e) => handleSearch(e.target.value)}
                    />
                  </InputGroup>
                </PopoverHeader>
                <PopoverCloseButton
                  top={2}
                  onClick={handleCancel}
                  data-testid="custom-report-popover-cancel"
                />
                <PopoverBody px={6} pt={5} pb={1}>
                  {isEmpty && (
                    <VStack
                      px={2}
                      pt={6}
                      pb={3}
                      data-testid="custom-reports-empty-state"
                    >
                      <Button
                        type="primary"
                        size="small"
                        aria-label={`add ${CUSTOM_REPORT_TITLE}`}
                        icon={<AddIcon />}
                        onClick={modalOnOpen}
                        className="rounded-full"
                        data-testid="add-report-button"
                      />
                      <Text fontSize="sm" textAlign="center" color="gray.500">
                        No {CUSTOM_REPORTS_TITLE.toLowerCase()} have been
                        created. Start by applying your preferred filter and
                        column settings, then create a{" "}
                        {CUSTOM_REPORT_TITLE.toLowerCase()} for easy access
                        later.
                      </Text>
                    </VStack>
                  )}
                  {!isEmpty &&
                    (isCustomReportsLoading ? (
                      <VStack pb={2}>
                        <Skeleton width="100%" height={theme.space[4]} />
                        <Skeleton width="100%" height={theme.space[4]} />
                        <Skeleton width="100%" height={theme.space[4]} />
                      </VStack>
                    ) : (
                      <Radio.Group
                        onChange={(e) => handleSelection(e.target.value)}
                        value={selectedReportId}
                        className="flex flex-col gap-2"
                      >
                        {searchResults?.map((customReport) => (
                          <Flex
                            key={customReport.id}
                            className={
                              userCanDeleteReports
                                ? "justify-between"
                                : "justify-start"
                            }
                          >
                            <Radio
                              value={customReport.id}
                              name="custom-report-id"
                              data-testid="custom-report-item"
                            >
                              <Text fontSize="sm">{customReport.name}</Text>
                            </Radio>
                            {userCanDeleteReports && (
                              <Button
                                type="text"
                                size="small"
                                icon={<TrashCanOutlineIcon fontSize={16} />}
                                onClick={() => setReportToDelete(customReport)}
                                data-testid="delete-report-button"
                              />
                            )}
                          </Flex>
                        ))}
                      </Radio.Group>
                    ))}
                </PopoverBody>
                <PopoverFooter border="none" px={6} pb={4} pt={4}>
                  <HStack>
                    {userCanCreateReports && tableStateToSave && (
                      <Button
                        size="small"
                        onClick={modalOnOpen}
                        className="w-full"
                        data-testid="create-report-button"
                        htmlType="button"
                      >
                        + Create {CUSTOM_REPORT_TITLE.toLowerCase()}
                      </Button>
                    )}
                    <Button
                      size="small"
                      type="primary"
                      loading={showSpinner}
                      disabled={applyDisabled}
                      className="w-full"
                      data-testid="apply-report-button"
                      htmlType="submit"
                    >
                      Apply
                    </Button>
                  </HStack>
                </PopoverFooter>
              </Form>
            </Formik>
          </PopoverContent>
        </Portal>
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
