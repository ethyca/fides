import {
  AntButton as Button,
  AntCol as Col,
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntRow as Row,
  AntUpload as Upload,
  AntUploadChangeParam as UploadChangeParam,
  AntUploadFile as UploadFile,
  Icons,
  useToast,
} from "fidesui";
import { CustomTypography } from "fidesui/src/hoc";
import { parse } from "papaparse";

import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
import { getErrorMessage } from "~/features/common/helpers";
import { InfoTooltip } from "~/features/common/InfoTooltip";
import { BackButtonNonLink } from "~/features/common/nav/BackButton";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useCreateSharedMonitorConfigMutation,
  useUpdateSharedMonitorConfigMutation,
} from "~/features/monitors/shared-monitor-config.slice";
import { SharedMonitorConfig } from "~/types/api/models/SharedMonitorConfig";
import { isErrorResult, RTKResult } from "~/types/errors";

export interface SharedMonitorConfigFormValues {
  name: string;
  description?: string | null;
  rules: {
    regex?: string;
    dataCategory?: string;
  }[];
}

const DEFAULT_INITIAL_VALUES: Partial<SharedMonitorConfigFormValues> = {
  rules: [{ regex: undefined, dataCategory: undefined }],
};

const FORM_COPY = `Match regular expressions to data categories to customize classification. Use the "shared monitor configuration" field when editing monitors to apply this configuration.`;

const TOOLTIP_COPY = `Upload a CSV to map regex patterns to data categories. Format: regex,data_category`;

const SharedMonitorConfigForm = ({
  config,
  onBackClick,
}: {
  config?: SharedMonitorConfig;
  onBackClick: () => void;
}) => {
  const [form] = Form.useForm<SharedMonitorConfigFormValues>();
  const toast = useToast();

  const [createMonitorTemplate, { isLoading: createIsLoading }] =
    useCreateSharedMonitorConfigMutation();
  const [updateMonitorTemplate, { isLoading: updateIsLoading }] =
    useUpdateSharedMonitorConfigMutation();

  const transformConfigResponseToFormValues = (
    response: SharedMonitorConfig,
  ): SharedMonitorConfigFormValues => {
    return {
      ...response,
      rules:
        response?.classify_params?.context_regex_pattern_mapping?.map(
          ([regex, dataCategory]) => ({
            regex,
            dataCategory,
          }),
        ) ?? [],
    };
  };

  const transformFormValuesToPayload = (
    values: SharedMonitorConfigFormValues,
  ): SharedMonitorConfig => {
    return {
      name: values.name,
      description: values.description,
      classify_params: {
        context_regex_pattern_mapping: values.rules.map(
          ({ regex, dataCategory }) => [regex, dataCategory],
        ),
      },
    };
  };

  const handleResult = (result: RTKResult, isCreate: boolean) => {
    if (isErrorResult(result)) {
      toast(
        errorToastParams(getErrorMessage(result.error, "A problem occurred")),
      );
    } else {
      toast(
        successToastParams(
          isCreate
            ? "Monitor config created successfully"
            : "Monitor config updated successfully",
        ),
      );
      onBackClick();
    }
  };

  const onSubmit = async (values: SharedMonitorConfigFormValues) => {
    const payload = transformFormValuesToPayload(values);
    let result;
    if (config) {
      result = await updateMonitorTemplate({ ...payload, id: config.id });
    } else {
      result = await createMonitorTemplate(payload);
    }
    handleResult(result, !config);
  };

  const handleFileUpload = (info: UploadChangeParam<UploadFile>) => {
    const { file } = info;
    if (!file) {
      return;
    }

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const csvText = e.target?.result as string;
        const { data } = parse<string[]>(csvText, {
          skipEmptyLines: true,
          header: false,
        });

        // Transform CSV data
        const rules = data.map(([regex, dataCategory]) => ({
          regex,
          dataCategory,
        }));

        // Update form with new rules
        form.setFieldValue("rules", rules);
        toast(successToastParams("CSV patterns imported successfully"));
      } catch (error) {
        toast(errorToastParams("Failed to parse CSV file"));
      }
    };
    reader.readAsText(file as any);
  };

  return (
    <>
      <BackButtonNonLink onClick={onBackClick} className="pt-3" />
      <CustomTypography.Title level={2}>
        {config ? `Edit ${config.name}` : "Create new configuration"}
      </CustomTypography.Title>
      <CustomTypography.Paragraph className="mt-2">
        {FORM_COPY}
      </CustomTypography.Paragraph>
      <Form
        name="monitor-template"
        layout="vertical"
        form={form}
        onFinish={onSubmit}
        className="mt-4"
        initialValues={
          config
            ? transformConfigResponseToFormValues(config)
            : DEFAULT_INITIAL_VALUES
        }
        validateTrigger={["onBlur", "onChange"]}
      >
        <Row>
          <Col span={24}>
            <Form.Item
              label="Configuration name"
              name="name"
              rules={[{ required: true, message: "Config name is required" }]}
              data-testid="form-item-name"
            >
              <Input autoFocus data-testid="input-name" />
            </Form.Item>
            <Form.Item
              label="Description"
              name="description"
              data-testid="form-item-description"
            >
              <Input.TextArea data-testid="input-description" />
            </Form.Item>
          </Col>
        </Row>
        <Form.List
          name="rules"
          rules={[
            {
              validator(_, value) {
                if (value.length === 0) {
                  return Promise.reject(
                    new Error("Please input at least one pattern"),
                  );
                }
                return Promise.resolve();
              },
            },
          ]}
        >
          {(fields, { add, remove }, { errors }) => (
            <>
              <Flex justify="space-between">
                <CustomTypography.Title level={3} className="pb-5">
                  Regex patterns
                </CustomTypography.Title>
                {!config && (
                  <Flex gap={8} align="center">
                    <InfoTooltip label={TOOLTIP_COPY} placement="left" />
                    <Upload
                      accept=".csv"
                      showUploadList={false}
                      beforeUpload={() => false}
                      onChange={handleFileUpload}
                    >
                      <Button
                        icon={<Icons.Upload />}
                        iconPosition="end"
                        size="small"
                        data-testid="upload-csv-btn"
                      >
                        Upload CSV
                      </Button>
                    </Upload>
                  </Flex>
                )}
              </Flex>
              {fields.map(({ key, name, ...field }, idx) => (
                <Row key={key} align="middle">
                  <Col span={11}>
                    <Form.Item
                      label="On match"
                      {...field}
                      name={[name, "regex"]}
                      rules={[{ required: true, message: "Regex is required" }]}
                      data-testid={`form-item-rules.${name}.regex`}
                    >
                      <Input
                        placeholder="Enter a regular expression"
                        data-testid={`input-rules.${name}.regex`}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={1} className="flex justify-center pt-[5px]">
                    -&gt;
                  </Col>
                  <Col span={11} className="pr-2">
                    <Form.Item
                      label="Assign"
                      {...field}
                      name={[name, "dataCategory"]}
                      rules={[
                        {
                          required: true,
                          message: "Data category is required",
                        },
                      ]}
                      data-testid={`form-item-rules.${name}.dataCategory`}
                    >
                      <DataCategorySelect
                        selectedTaxonomies={[]}
                        variant="outlined"
                        placeholder="Select a data category"
                        autoFocus={false}
                        allowClear
                        data-testid={`input-rules.${name}.dataCategory`}
                      />
                    </Form.Item>
                  </Col>
                  <Col span={1} className="mt-[7.25px]">
                    {idx === fields.length - 1 ? (
                      <Button
                        onClick={() => add()}
                        icon={<Icons.Add />}
                        aria-label="Add new rule"
                        data-testid="add-rule-btn"
                      />
                    ) : (
                      <Button
                        onClick={() => remove(name)}
                        icon={<Icons.TrashCan />}
                        aria-label="Remove rule"
                        data-testid={`remove-rule-${name}`}
                      />
                    )}
                  </Col>
                </Row>
              ))}
              <Form.ErrorList errors={errors} />
              <Form.Item label={null} className="mb-0">
                <Flex justify="end" gap={8}>
                  <Button onClick={onBackClick}>Cancel</Button>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={createIsLoading || updateIsLoading}
                    data-testid="save-btn"
                  >
                    Save
                  </Button>
                </Flex>
              </Form.Item>
            </>
          )}
        </Form.List>
      </Form>
    </>
  );
};

export default SharedMonitorConfigForm;
