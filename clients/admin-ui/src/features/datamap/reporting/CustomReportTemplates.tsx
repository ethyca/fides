import {
  Button,
  ChevronDownIcon,
  ConfirmationModal,
  HStack,
  IconButton,
  Popover,
  PopoverArrow,
  PopoverBody,
  PopoverCloseButton,
  PopoverContent,
  PopoverFooter,
  PopoverHeader,
  PopoverTrigger,
  Portal,
  Radio,
  RadioGroup,
  Skeleton,
  Text,
  theme,
  useDisclosure,
  useToast,
  VStack,
} from "fidesui";
import { Form, Formik } from "formik";
import { useEffect, useState } from "react";

import { AddIcon } from "~/features/common/custom-fields/icons/AddIcon";
import { getErrorMessage } from "~/features/common/helpers";
import { TrashCanOutlineIcon } from "~/features/common/Icon/TrashCanOutlineIcon";
import { useHasPermission } from "~/features/common/Restrict";
import {
  CustomReportResponse,
  CustomReportResponseMinimal,
  ScopeRegistryEnum,
} from "~/types/api";

import { CustomReportTableState } from "../types";
import {
  useDeleteCustomReportMutation,
  useGetMinimalCustomReportsQuery,
  useLazyGetCustomReportByIdQuery,
} from "./custom-reports.slice";
import { CustomReportCreationModal } from "./CustomReportCreationModal";

const CUSTOM_REPORT_TITLE = "Report";
const CUSTOM_REPORTS_TITLE = "Reports";

interface CustomReportTemplatesProps {
  savedReportId: string; // from local storage
  tableStateToSave: CustomReportTableState | undefined;
  currentColumnMap: Record<string, string> | undefined;
  onCustomReportSaved: (customReport: CustomReportResponse) => void;
  onSavedReportDeleted: () => void;
}

export const CustomReportTemplates = ({
  savedReportId,
  tableStateToSave,
  currentColumnMap,
  onCustomReportSaved,
  onSavedReportDeleted,
}: CustomReportTemplatesProps) => {
  const userCanSeeReports = useHasPermission([
    ScopeRegistryEnum.CUSTOM_REPORT_READ,
  ]);
  const userCanCreateReports = useHasPermission([
    ScopeRegistryEnum.CUSTOM_REPORT_CREATE,
  ]);
  const userCanDeleteReports = useHasPermission([
    ScopeRegistryEnum.CUSTOM_REPORT_DELETE,
  ]);

  const toast = useToast({ id: "custom-report-toast" });

  const { data: customReportsResponse, isLoading: isCustomReportsLoading } =
    useGetMinimalCustomReportsQuery({});
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

  // TASK: Doesn’t show as applied when saving the first time
  // TASK: pass `report_id` to download reports endpoint
  // TASK: Add checking other options once report is applied

  const [selectedReportId, setSelectedReportId] = useState<string>(); // for the radio buttons
  const [fetchedReport, setFetchedReport] = useState<CustomReportResponse>();
  const [reportToDelete, setReportToDelete] =
    useState<CustomReportResponseMinimal>();
  const [showSpinner, setShowSpinner] = useState<boolean>(false);

  const isEmpty =
    !isCustomReportsLoading && !customReportsResponse?.items?.length;

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
    setSelectedReportId(undefined);
    setFetchedReport(undefined);
    setShowSpinner(false);
  };

  const handleApplyTemplate = () => {
    if (fetchedReport) {
      setShowSpinner(false);
      if (fetchedReport.id !== savedReportId) {
        onCustomReportSaved(fetchedReport);
      }
      popoverOnClose();
    } else if (selectedReportId) {
      setShowSpinner(true);
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

  if (!userCanSeeReports) {
    return null;
  }

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
            size="xs"
            variant="outline"
            maxWidth={150}
            rightIcon={<ChevronDownIcon />}
            data-testid="custom-reports-trigger"
            onClick={popoverOnToggle}
          >
            <Text noOfLines={1}>
              {fetchedReport ? fetchedReport.name : CUSTOM_REPORTS_TITLE}
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
                  size="xs"
                  variant="outline"
                  isDisabled={isEmpty}
                  sx={{ pos: "absolute", top: 2, left: 2 }}
                  type="reset"
                >
                  Reset
                </Button>
                <PopoverHeader textAlign="center">
                  <Text fontSize="sm">{CUSTOM_REPORTS_TITLE}</Text>
                </PopoverHeader>
                <PopoverCloseButton top={2} onClick={popoverOnClose} />
                <PopoverBody px={6} pt={3} pb={1}>
                  {isEmpty && (
                    <VStack
                      px={2}
                      pt={6}
                      pb={3}
                      data-testid="custom-reports-empty-state"
                    >
                      <IconButton
                        variant="primary"
                        backgroundColor="gray.500"
                        isRound
                        size="xs"
                        aria-label={`add ${CUSTOM_REPORT_TITLE}`}
                        icon={<AddIcon />}
                        onClick={modalOnOpen}
                        data-testid="add-report-button"
                      />
                      <Text fontSize="sm" textAlign="center" color="gray.500">
                        No {CUSTOM_REPORTS_TITLE.toLowerCase()} have been
                        created. Start by applying your preferred filter and
                        column settings, then create a
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
                      <RadioGroup
                        onChange={handleSelection}
                        value={selectedReportId}
                      >
                        {customReportsResponse?.items.map((customReport) => (
                          <HStack
                            key={customReport.id}
                            justifyContent={
                              userCanDeleteReports
                                ? "space-between"
                                : "flex-start"
                            }
                            min-height={theme.space[6]}
                          >
                            <Radio
                              name="custom-report-id"
                              value={customReport.id}
                              data-testid="custom-report-item"
                            >
                              <Text fontSize="xs">{customReport.name}</Text>
                            </Radio>
                            {userCanDeleteReports && (
                              <IconButton
                                variant="ghost"
                                size="xs"
                                aria-label={`delete ${CUSTOM_REPORT_TITLE}`}
                                icon={<TrashCanOutlineIcon fontSize={16} />}
                                onClick={() => {
                                  setReportToDelete(customReport);
                                }}
                                data-testid="delete-report-button"
                              />
                            )}
                          </HStack>
                        ))}
                      </RadioGroup>
                    ))}
                </PopoverBody>
                <PopoverFooter border="none" px={6}>
                  <HStack>
                    {userCanCreateReports && tableStateToSave && (
                      <Button
                        size="xs"
                        variant="outline"
                        onClick={modalOnOpen}
                        width="100%"
                        data-testid="create-report-button"
                        type="button"
                      >
                        + Create {CUSTOM_REPORT_TITLE.toLowerCase()}
                      </Button>
                    )}
                    <Button
                      size="xs"
                      variant="primary"
                      isLoading={showSpinner}
                      isDisabled={!fetchedReport}
                      width="100%"
                      data-testid="apply-report-button"
                      type="submit"
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
        unavailableNames={customReportsResponse?.items.map((customReport) => {
          return customReport.name;
        })}
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
