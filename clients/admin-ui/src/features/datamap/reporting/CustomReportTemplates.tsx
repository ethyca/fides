import { TableState } from "@tanstack/react-table";
import {
  Button,
  ChevronDownIcon,
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
import { useLocalStorage } from "~/features/common/hooks/useLocalStorage";
import { TrashCanOutlineIcon } from "~/features/common/Icon/TrashCanOutlineIcon";
import { CustomReportResponse } from "~/types/api";

import { DATAMAP_LOCAL_STORAGE_KEYS } from "../constants";
import {
  useGetMinimalCustomReportsQuery,
  useLazyGetCustomReportByIdQuery,
} from "./custom-reports.slice";
import { CustomReportCreationModal } from "./CustomReportCreationModal";

const CUSTOM_REPORT_TITLE = "Report";
const CUSTOM_REPORTS_TITLE = "Reports";

interface CustomReportTemplatesProps {
  currentTableState: TableState | undefined;
  currentColumnMap: Record<string, string> | undefined;
  onTemplateApplied: (customReport: CustomReportResponse) => void;
}

export const CustomReportTemplates = ({
  currentTableState,
  currentColumnMap,
  onTemplateApplied,
}: CustomReportTemplatesProps) => {
  // TASK: Implement permissions for creating and deleting custom reports (contributor and owner roles)
  const toast = useToast({ id: "custom-report-toast" });
  const { data: customReportsResponse, isLoading: isCustomReportsLoading } =
    useGetMinimalCustomReportsQuery({});
  const [getCustomReportByIdTrigger] = useLazyGetCustomReportByIdQuery();
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

  const [selectedReportId, setSelectedReportId] = useLocalStorage<string>(
    DATAMAP_LOCAL_STORAGE_KEYS.CUSTOM_REPORT_ID,
    "",
  );

  const [selectedReport, setSelectedReport] = useState<CustomReportResponse>();

  const [showSpinner, setShowSpinner] = useState<boolean>(false);

  const isEmpty =
    !isCustomReportsLoading && !customReportsResponse?.items?.length;

  // TASK: can we reset the selected template when user manually updates the table state?

  const handleSelection = async (id: string) => {
    setSelectedReportId(id);
  };

  const handleApplyTemplate = () => {
    if (selectedReport) {
      setShowSpinner(false);
      onTemplateApplied(selectedReport);
      popoverOnClose();
      toast({ status: "success", description: "Report applied successfully." });
    } else {
      setShowSpinner(true);
    }
  };

  const handleCloseModal = () => {
    modalOnClose();
    setTimeout(() => {
      // switch back to the popover once the modal has closed
      popoverOnOpen();
    }, 100);
  };

  const getCustomReportById = async (id: string) => {
    const { data, isError, error } = await getCustomReportByIdTrigger(id);
    if (isError) {
      const errorMsg = getErrorMessage(
        error,
        `A problem occurred while fetching the ${CUSTOM_REPORT_TITLE}.`,
      );
      toast({ status: "error", description: errorMsg });
    } else {
      setSelectedReport(data);
    }
  };

  useEffect(() => {
    // If the user clicks the apply button before the report is fetched, the spinner will show. Once the selected report is fetched, stop the spinner and apply the template.
    if (showSpinner) {
      setShowSpinner(false);
      handleApplyTemplate();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedReport]);

  useEffect(() => {
    if (selectedReportId) {
      // prefetch the selected report when the user selects it so that it's ready to apply faster
      getCustomReportById(selectedReportId);
    } else {
      // if the user resets the selected report ID, clear the selected report state as well.
      setSelectedReport(undefined);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedReportId]);

  useEffect(() => {
    if (customReportsResponse?.items?.length) {
      const selectedIdExists = customReportsResponse.items.some(
        (customReport) => customReport.id === selectedReportId,
      );
      if (!selectedIdExists) {
        setSelectedReportId("");
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customReportsResponse]);

  return (
    <>
      <Popover
        placement="bottom-end"
        isOpen={popoverIsOpen}
        id="custom-reports-selection"
      >
        <PopoverTrigger>
          <Button
            size="xs"
            variant="outline"
            rightIcon={<ChevronDownIcon />}
            data-testid="custom-reports-trigger"
            onClick={popoverOnToggle}
          >
            {CUSTOM_REPORTS_TITLE}
          </Button>
        </PopoverTrigger>
        <Portal>
          <PopoverContent data-testid="custom-reports-popover">
            <PopoverArrow />
            <Formik
              initialValues={{}}
              onSubmit={handleApplyTemplate}
              onReset={() => {
                setSelectedReportId("");
              }}
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
                            justifyContent="space-between"
                          >
                            <Radio
                              name="custom-report-id"
                              value={customReport.id}
                              data-testid="custom-report-item"
                            >
                              <Text fontSize="xs" lineHeight={6}>
                                {customReport.name}
                              </Text>
                            </Radio>
                            <IconButton
                              variant="ghost"
                              size="xs"
                              aria-label={`delete ${CUSTOM_REPORT_TITLE}`}
                              icon={<TrashCanOutlineIcon fontSize={16} />}
                              onClick={() => {
                                // TASK: delete the report
                                console.log("delete report");
                              }}
                              data-testid="delete-report-button"
                            />
                          </HStack>
                        ))}
                      </RadioGroup>
                    ))}
                </PopoverBody>
                <PopoverFooter border="none" px={6}>
                  <HStack>
                    {currentTableState && (
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
                      isDisabled={!selectedReportId}
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
        tableStateToSave={currentTableState}
        columnMapToSave={currentColumnMap}
        unavailableNames={customReportsResponse?.items.map((customReport) => {
          return customReport.name;
        })}
      />
    </>
  );
};
