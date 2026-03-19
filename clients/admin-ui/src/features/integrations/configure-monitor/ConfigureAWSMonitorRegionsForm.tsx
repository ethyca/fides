import { Button, Form, Select } from "fidesui";
import { useEffect, useState } from "react";

import { useGetInfraMonitorRegionsQuery } from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { EditableMonitorConfig } from "~/types/api";

const ConfigureAWSMonitorRegionsForm = ({
  monitor,
  isSubmitting,
  onClose,
  onSubmit,
}: {
  monitor: EditableMonitorConfig;
  isSubmitting?: boolean;
  onClose: () => void;
  onSubmit: (regions: string[]) => void;
}) => {
  const [form] = Form.useForm<{ regions: string[] }>();
  const [submittable, setSubmittable] = useState(true);
  const formValues = Form.useWatch([], form);

  const { data: regionsData, isFetching: isLoadingRegions } =
    useGetInfraMonitorRegionsQuery(
      { key: monitor.key! },
      { skip: !monitor.key },
    );

  const regionOptions = (regionsData?.regions || []).map((r) => ({
    label: r,
    value: r,
  }));

  const existingRegions =
    (monitor.datasource_params as { regions?: string[] } | undefined)
      ?.regions ?? [];

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, formValues]);

  const handleFinish = (values: { regions: string[] }) => {
    onSubmit(values.regions ?? []);
  };

  return (
    <Form
      form={form}
      onFinish={handleFinish}
      className="pt-4"
      layout="vertical"
      initialValues={{ regions: existingRegions }}
    >
      <Form.Item
        label="Regions"
        name="regions"
        tooltip="Select specific AWS regions to scan. Leave empty to use an aggregator index covering all regions."
      >
        <Select
          mode="multiple"
          aria-label="Select AWS regions"
          data-testid="controlled-select-regions"
          options={regionOptions}
          loading={isLoadingRegions}
          placeholder={
            isLoadingRegions
              ? "Loading regions…"
              : "All regions (via aggregator index)"
          }
          optionFilterProp="label"
          allowClear
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
          data-testid="save-btn"
        >
          Save
        </Button>
      </div>
    </Form>
  );
};

export default ConfigureAWSMonitorRegionsForm;
