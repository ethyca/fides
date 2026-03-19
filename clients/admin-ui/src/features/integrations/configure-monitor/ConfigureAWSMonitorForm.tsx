import { Button, DatePicker, Form, Input, Select } from "fidesui";
import type { Dayjs } from "dayjs";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";

import { enumToOptions, formatUser } from "~/features/common/helpers";
import { useGetAllUsersQuery } from "~/features/user-management";
import { EditableMonitorConfig, MonitorFrequency } from "~/types/api";
import { useEffect, useState } from "react";
import { useRouter } from "next/router";

import { START_TIME_TOOLTIP_COPY } from "./ConfigureWebsiteMonitorForm";

dayjs.extend(utc);

interface AWSMonitorFormValues {
  name: string;
  execution_frequency?: MonitorFrequency;
  execution_start_date: Dayjs;
  stewards?: string[];
}

const ConfigureAWSMonitorForm = ({
  monitor,
  isSubmitting,
  onClose,
  onSubmit,
}: {
  monitor?: EditableMonitorConfig;
  isSubmitting?: boolean;
  onClose: () => void;
  onSubmit: (monitor: EditableMonitorConfig) => void;
}) => {
  const isEditing = !!monitor;
  const router = useRouter();
  const integrationId = Array.isArray(router.query.id)
    ? router.query.id[0]
    : router.query.id;

  const [form] = Form.useForm<AWSMonitorFormValues>();
  const [submittable, setSubmittable] = useState(false);
  const formValues = Form.useWatch([], form);

  const { data: eligibleUsersData } = useGetAllUsersQuery({
    page: 1,
    size: 100,
    include_external: false,
    exclude_approvers: true,
  });

  const dataStewardOptions = (eligibleUsersData?.items || []).map((user) => ({
    label: formatUser(user),
    value: user.id,
  }));

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, formValues]);

  const handleFinish = (values: AWSMonitorFormValues) => {
    const executionInfo =
      values.execution_frequency !== MonitorFrequency.NOT_SCHEDULED
        ? {
            execution_frequency: values.execution_frequency,
            execution_start_date: values.execution_start_date
              .utc()
              .format("YYYY-MM-DD[T]HH:mm:ss[Z]"),
          }
        : {
            execution_frequency: MonitorFrequency.NOT_SCHEDULED,
            execution_start_date: undefined,
          };

    const payload: EditableMonitorConfig = isEditing
      ? {
          ...monitor,
          ...executionInfo,
          name: values.name,
          stewards: values.stewards,
        }
      : {
          ...executionInfo,
          name: values.name,
          connection_config_key: integrationId!,
          stewards: values.stewards,
        };

    onSubmit(payload);
  };

  const initialValues = {
    name: monitor?.name,
    execution_start_date: dayjs(monitor?.execution_start_date ?? undefined),
    execution_frequency:
      monitor?.execution_frequency ?? MonitorFrequency.MONTHLY,
    stewards: monitor?.stewards,
  } as const;

  return (
    <Form
      form={form}
      onFinish={handleFinish}
      className="pt-4"
      layout="vertical"
      validateTrigger="onChange"
      initialValues={initialValues}
    >
      <Form.Item
        label="Name"
        name="name"
        rules={[{ required: true, message: "Please enter a name" }]}
      >
        <Input data-testid="input-name" />
      </Form.Item>
      <Form.Item label="Stewards" name="stewards">
        <Select
          mode="multiple"
          aria-label="Select stewards"
          options={dataStewardOptions}
          optionFilterProp="label"
        />
      </Form.Item>
      <Form.Item
        label="Automatic execution frequency"
        name="execution_frequency"
        tooltip="Interval to run the monitor automatically after the start date"
      >
        <Select
          aria-label="Select automatic execution frequency"
          options={enumToOptions(MonitorFrequency)}
        />
      </Form.Item>
      <Form.Item
        label="Automatic execution start time"
        name="execution_start_date"
        tooltip={START_TIME_TOOLTIP_COPY}
      >
        <DatePicker
          disabled={
            form.getFieldValue("execution_frequency") ===
            MonitorFrequency.NOT_SCHEDULED
          }
          showTime
          className="w-full"
        />
      </Form.Item>
      <div className="flex w-full justify-between">
        <Button
          onClick={() => {
            form.resetFields();
            onClose();
          }}
        >
          Cancel
        </Button>
        <Button
          htmlType="submit"
          type="primary"
          disabled={!submittable}
          loading={isSubmitting}
          data-testid="next-btn"
        >
          Next
        </Button>
      </div>
    </Form>
  );
};

export default ConfigureAWSMonitorForm;
