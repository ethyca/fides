import {
  Button,
  Flex,
  Form,
  Input,
  Modal,
  Paragraph,
  useMessage,
} from "fidesui";
import { useEffect, useMemo, useState } from "react";

import { CustomReportColumn } from "~/features/common/custom-reports/types";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { CustomReportResponse, ReportType } from "~/types/api";

import { usePostCustomReportMutation } from "../../datamap/reporting/custom-reports.slice";
import { CustomReportTableState } from "../../datamap/types";

const CUSTOM_REPORT_LABEL = "Report name";

interface FormValues {
  reportName: string;
}

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
  const message = useMessage();
  const [form] = Form.useForm<FormValues>();
  const allValues = Form.useWatch([], form);
  const [submittable, setSubmittable] = useState(false);

  const [postCustomReportMutationTrigger, { isLoading: isCreating }] =
    usePostCustomReportMutation();

  const reportNameRules = useMemo(
    () => [
      {
        required: true,
        message: "Please provide a name for this report",
      },
      {
        max: 80,
        message: "Report name is too long (max 80 characters)",
      },
      {
        validator: (_: unknown, value: string) => {
          if (value && unavailableNames?.includes(value)) {
            return Promise.reject(new Error("This name already exists"));
          }
          return Promise.resolve();
        },
      },
    ],
    [unavailableNames],
  );

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, allValues]);

  const handleFinish = async (values: FormValues) => {
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
        name: values.reportName.trim(),
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
      message.error(errorMsg);
    }
  };

  return (
    <Modal
      open={isOpen}
      onCancel={handleClose}
      title="Create a report"
      footer={null}
      centered
      destroyOnHidden
      afterOpenChange={(open) => {
        if (!open) {
          form.resetFields();
        }
      }}
    >
      <Form
        form={form}
        layout="vertical"
        initialValues={{ reportName: "" }}
        onFinish={handleFinish}
        data-testid="custom-report-form"
      >
        <Paragraph type="secondary">
          Customize and save your current filter settings for easy access in the
          future. This saved report will include the column layout and currently
          applied filter settings.
        </Paragraph>
        <Form.Item
          name="reportName"
          label={CUSTOM_REPORT_LABEL}
          rules={reportNameRules}
          required
        >
          <Input
            placeholder="Enter a name for the report..."
            maxLength={80}
            data-testid="input-reportName"
          />
        </Form.Item>
        <Flex justify="flex-end" gap="small" className="mt-4">
          <Button onClick={handleClose}>Cancel</Button>
          <Button
            disabled={!submittable}
            loading={isCreating}
            type="primary"
            data-testid="custom-report-form-submit"
            htmlType="submit"
          >
            Save
          </Button>
        </Flex>
      </Form>
    </Modal>
  );
};
