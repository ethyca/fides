import { TableState } from "@tanstack/react-table";
import {
  Button,
  ChevronDownIcon,
  HStack,
  IconButton,
  List,
  ListItem,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Popover,
  PopoverArrow,
  PopoverBody,
  PopoverCloseButton,
  PopoverContent,
  PopoverFooter,
  PopoverHeader,
  PopoverTrigger,
  Portal,
  Text,
  useDisclosure,
  VStack,
} from "fidesui";
import { Form, Formik } from "formik";
import { useMemo, useState } from "react";
import * as Yup from "yup";

import { AddIcon } from "~/features/common/custom-fields/icons/AddIcon";
import { CustomTextInput } from "~/features/common/form/inputs";

const CUSTOM_REPORT_LABEL = "Report name";
const CUSTOM_REPORTS_TITLE = "Reports";

// TASK: get this interface from the schema
type CustomReportTemplate = {
  id: string;
  name: string;
  type?: never;
  created_by?: never;
  config?: {
    column_map?: Record<string, string> | null;
    table_state?: TableState | null;
  };
};

interface CustomReportTemplatesProps {
  currentTableState: TableState | undefined;
  onTemplateSelected: (template: CustomReportTemplate) => void;
}

export const CustomReportTemplates = ({
  currentTableState,
  onTemplateSelected,
}: CustomReportTemplatesProps) => {
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
    getDisclosureProps: getModalDisclosureProps,
  } = useDisclosure();

  const [availableTemplates, setAvailableTemplates] = useState<
    CustomReportTemplate[]
  >([]);

  const isEmpty = !availableTemplates || availableTemplates.length === 0;

  const ValidationSchema = useMemo(
    () =>
      Yup.object().shape({
        reportName: Yup.string()
          .required()
          .label(CUSTOM_REPORT_LABEL)
          .test("is-unique", "", async (value, context) => {
            if (
              availableTemplates
                .map((template) => {
                  return template.name;
                })
                .includes(value)
            ) {
              return context.createError({
                message: `${CUSTOM_REPORT_LABEL} "${value}" is already being used. Please provide a unique value.`,
              });
            }
            return true;
          }),
      }),
    [availableTemplates],
  );

  const handleTemplateSelection = (template: CustomReportTemplate) => {
    onTemplateSelected(template);
    popoverOnClose();
  };

  const handleCloseModal = () => {
    modalOnClose();
    setTimeout(() => {
      // switch back to the popover once the modal has closed
      popoverOnOpen();
    }, 100);
  };

  const handleCreateReport = () => {
    handleCloseModal();
  };

  return (
    <>
      <Popover
        placement="bottom-end"
        isOpen={popoverIsOpen}
        onClose={popoverOnClose}
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
            <Button
              size="xs"
              variant="outline"
              isDisabled={isEmpty}
              sx={{ pos: "absolute", top: 2, left: 2 }}
            >
              Reset
            </Button>
            <PopoverHeader textAlign="center">
              <Text fontSize="sm">{CUSTOM_REPORTS_TITLE}</Text>
            </PopoverHeader>
            <PopoverCloseButton top={2} />
            <PopoverBody>
              {isEmpty ? (
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
                    aria-label="add report"
                    icon={<AddIcon />}
                    onClick={modalOnOpen}
                    data-testid="add-report-button"
                  />
                  <Text fontSize="sm" textAlign="center" color="gray.500">
                    No Reporting templates have been created. Start by applying
                    your preferred filter and column settings, then create a
                    report for easy access later.
                  </Text>
                </VStack>
              ) : (
                <List>
                  {availableTemplates.map((template) => (
                    <ListItem key={template.id}>
                      <Button
                        size="xs"
                        variant="outline"
                        onClick={() => handleTemplateSelection(template)}
                      >
                        {template.name}
                      </Button>
                    </ListItem>
                  ))}
                </List>
              )}
            </PopoverBody>
            <PopoverFooter border="none">
              <HStack>
                {currentTableState && (
                  <Button
                    size="xs"
                    variant="outline"
                    onClick={modalOnOpen}
                    width="100%"
                  >
                    + Create report
                  </Button>
                )}
                <Button
                  size="xs"
                  variant="primary"
                  isDisabled={isEmpty}
                  onClick={() =>
                    handleTemplateSelection({ id: "test", name: "test" })
                  }
                  width="100%"
                >
                  Apply
                </Button>
              </HStack>
            </PopoverFooter>
          </PopoverContent>
        </Portal>
      </Popover>
      <Modal
        size="lg"
        isOpen={modalIsOpen}
        onClose={handleCloseModal}
        motionPreset="none"
      >
        <ModalOverlay />
        <ModalContent>
          <ModalHeader pb={0}>Create a report</ModalHeader>
          <Formik
            initialValues={{
              reportName: "",
            }}
            onSubmit={(values) => {
              // Task: save the report
              console.log(values.reportName, currentTableState);
            }}
            validateOnBlur={false}
            validationSchema={ValidationSchema}
          >
            {({ dirty, isValid, resetForm }) => (
              <Form>
                <ModalBody>
                  <Text fontSize="sm" color="gray.600" pb={6}>
                    Customize and save your current filter settings for easy
                    access in the future. This reporting template will save the
                    column layout and currently applied filter settings.
                  </Text>
                  <CustomTextInput
                    id="reportName"
                    name="reportName"
                    isRequired
                    label={CUSTOM_REPORT_LABEL}
                    placeholder="Enter a name for the report..."
                    variant="stacked"
                  />
                </ModalBody>
                <ModalFooter gap={2}>
                  <Button
                    size="xs"
                    variant="outline"
                    onClick={() => {
                      resetForm();
                      handleCloseModal();
                    }}
                  >
                    Cancel
                  </Button>
                  <Button
                    size="xs"
                    isDisabled={!dirty || !isValid}
                    variant="primary"
                    onClick={handleCreateReport}
                    type="submit"
                  >
                    Save
                  </Button>
                </ModalFooter>
              </Form>
            )}
          </Formik>
        </ModalContent>
      </Modal>
    </>
  );
};
