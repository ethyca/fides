import { TableState } from "@tanstack/react-table";
import {
  Button,
  Modal,
  ModalBody,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalOverlay,
  Text,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import { useMemo } from "react";
import * as Yup from "yup";

import { CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage } from "~/features/common/helpers";
import { ReportType } from "~/types/api";

import { usePostCustomReportMutation } from "./custom-reports.slice";

const CUSTOM_REPORT_LABEL = "Report name";

interface CustomReportCreationModalProps {
  isOpen: boolean;
  handleClose: () => void;
  tableStateToSave: TableState | undefined;
  columnMapToSave: Record<string, string> | undefined;
  unavailableNames?: string[];
}

export const CustomReportCreationModal = ({
  isOpen,
  handleClose,
  tableStateToSave,
  columnMapToSave,
  unavailableNames,
}: CustomReportCreationModalProps) => {
  const toast = useToast();

  const [postCustomReportMutationTrigger] = usePostCustomReportMutation();

  const ValidationSchema = useMemo(
    () =>
      Yup.object().shape({
        reportName: Yup.string()
          .required()
          .label(CUSTOM_REPORT_LABEL)
          .test("is-unique", "", async (value, context) => {
            if (unavailableNames?.includes(value)) {
              return context.createError({
                message: `${CUSTOM_REPORT_LABEL} "${value}" is already being used. Please provide a unique value.`,
              });
            }
            return true;
          }),
      }),
    [unavailableNames],
  );

  const handleCreateReport = async (reportName: string) => {
    try {
      await postCustomReportMutationTrigger({
        name: reportName,
        type: ReportType.DATAMAP,
        config: {
          column_map: columnMapToSave,
          table_state: tableStateToSave,
        },
      });
      handleClose();
    } catch (error: any) {
      const errorMsg = getErrorMessage(
        error,
        "A problem occurred while creating the report.",
      );
      toast({ status: "error", description: errorMsg });
    }
  };

  return (
    <Modal size="lg" isOpen={isOpen} onClose={handleClose} motionPreset="none">
      <ModalOverlay />
      <ModalContent>
        <ModalHeader pb={0}>Create a report</ModalHeader>
        <Formik
          initialValues={{
            reportName: "",
          }}
          onSubmit={(values) => handleCreateReport(values.reportName)}
          onReset={handleClose}
          validateOnBlur={false}
          validationSchema={ValidationSchema}
        >
          {({ dirty, isValid }) => (
            <Form data-testid="custom-report-form">
              <ModalBody>
                <Text fontSize="sm" color="gray.600" pb={6}>
                  Customize and save your current filter settings for easy
                  access in the future. This reporting customReport will save
                  the column layout and currently applied filter settings.
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
                <Button size="xs" variant="outline" type="reset">
                  Cancel
                </Button>
                <Button
                  size="xs"
                  isDisabled={!dirty || !isValid}
                  variant="primary"
                  data-testid="custom-report-form-submit"
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
  );
};
