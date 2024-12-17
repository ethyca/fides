import {
  AntButton as Button,
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

import { CustomReportColumn } from "~/features/common/custom-reports/CustomReportColumn";
import { CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { CustomReportResponse, ReportType } from "~/types/api";

import { usePostCustomReportMutation } from "../../datamap/reporting/custom-reports.slice";
import { CustomReportTableState } from "../../datamap/types";

const CUSTOM_REPORT_LABEL = "Report name";

interface CustomReportCreationModalProps {
  isOpen: boolean;
  handleClose: () => void;
  tableStateToSave: CustomReportTableState | undefined;
  columnMapToSave: Record<string, string> | undefined;
  unavailableNames?: string[];
  onCreateCustomReport: (newReport: CustomReportResponse) => void;
}

export const CustomReportCreationModal = ({
  isOpen,
  handleClose,
  tableStateToSave,
  columnMapToSave = {},
  unavailableNames,
  onCreateCustomReport,
}: CustomReportCreationModalProps) => {
  const toast = useToast();

  const [postCustomReportMutationTrigger] = usePostCustomReportMutation();

  const ValidationSchema = useMemo(
    () =>
      Yup.object().shape({
        reportName: Yup.string()
          .label(CUSTOM_REPORT_LABEL)
          .required("Please provide a name for this report")
          .test("is-unique", "", async (value, context) => {
            if (unavailableNames?.includes(value)) {
              return context.createError({
                message: `This name already exists`,
              });
            }
            return true;
          })
          .max(80, "Report name is too long (max 80 characters)"),
      }),
    [unavailableNames],
  );

  const handleCreateReport = async (reportName: string) => {
    const newColumnMap: Record<string, CustomReportColumn> = {};
    Object.entries(columnMapToSave).forEach(([key, value]) => {
      newColumnMap[key] = {
        label: value,
        enabled: true,
      };
    });
    Object.entries(tableStateToSave?.columnVisibility ?? {}).forEach(
      ([key, value]) => {
        if (!newColumnMap[key]) {
          newColumnMap[key] = {};
        }
        newColumnMap[key].enabled = value;
      },
    );
    try {
      const newReportTemplate = {
        name: reportName.trim(),
        type: ReportType.DATAMAP,
        config: {
          column_map: newColumnMap,
          table_state: tableStateToSave,
        },
      };
      const result = await postCustomReportMutationTrigger(newReportTemplate);
      if (isErrorResult(result)) {
        throw result.error as Error;
      }
      onCreateCustomReport(result.data);
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
                  access in the future. This saved report will include the
                  column layout and currently applied filter settings.
                </Text>
                <CustomTextInput
                  id="reportName"
                  name="reportName"
                  isRequired
                  label={CUSTOM_REPORT_LABEL}
                  placeholder="Enter a name for the report..."
                  variant="stacked"
                  maxLength={80}
                />
              </ModalBody>
              <ModalFooter gap={2}>
                <Button size="small" htmlType="reset">
                  Cancel
                </Button>
                <Button
                  size="small"
                  disabled={!dirty || !isValid}
                  type="primary"
                  data-testid="custom-report-form-submit"
                  htmlType="submit"
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
