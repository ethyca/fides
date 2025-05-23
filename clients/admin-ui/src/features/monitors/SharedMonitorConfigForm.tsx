import {
  AntButton,
  AntCol,
  AntFlex,
  AntForm,
  AntInput,
  AntRow,
  AntUpload,
  Icons,
  useToast,
} from "fidesui";
import { CustomTypography } from "fidesui/src/hoc";

import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
import { getErrorMessage } from "~/features/common/helpers";
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

const SharedMonitorConfigForm = ({
  config,
  onBackClick,
}: {
  config?: SharedMonitorConfig;
  onBackClick: () => void;
}) => {
  const [form] = AntForm.useForm<SharedMonitorConfigFormValues>();
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

  return (
    <>
      <BackButtonNonLink onClick={onBackClick} className="pt-3" />
      <CustomTypography.Title level={2}>
        {config ? `Edit ${config.name}` : "Create new configuration"}
      </CustomTypography.Title>
      <CustomTypography.Paragraph className="mt-2">
        {FORM_COPY}
      </CustomTypography.Paragraph>
      <AntForm
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
        <AntRow>
          <AntCol span={24}>
            <AntForm.Item
              label="Configuration name"
              name="name"
              rules={[{ required: true, message: "Config name is required" }]}
            >
              <AntInput autoFocus />
            </AntForm.Item>
            <AntForm.Item label="Description" name="description">
              <AntInput.TextArea />
            </AntForm.Item>
          </AntCol>
        </AntRow>
        <AntForm.List
          name="rules"
          rules={[
            {
              validator(_, value) {
                if (value.length === 0) {
                  return Promise.reject(
                    new Error("Please input at least one rule"),
                  );
                }
                return Promise.resolve();
              },
            },
          ]}
        >
          {(fields, { add, remove }, { errors }) => (
            <>
              <AntFlex justify="space-between">
                <CustomTypography.Title level={3} className="pb-4">
                  Regex patterns
                </CustomTypography.Title>
                {!config && (
                  <AntUpload onChange={(e) => console.log("change", e)}>
                    <AntButton icon={<Icons.Upload />} iconPosition="end">
                      Upload CSV
                    </AntButton>
                  </AntUpload>
                )}
              </AntFlex>
              {fields.map(({ key, name, ...field }, idx) => (
                <AntRow key={key} gutter={8} align="middle">
                  <AntCol span={11}>
                    <AntForm.Item
                      label="On match"
                      {...field}
                      name={[name, "regex"]}
                      rules={[{ required: true, message: "Regex is required" }]}
                    >
                      <AntInput placeholder="Enter a regular expression" />
                    </AntForm.Item>
                  </AntCol>
                  <AntCol span={1} className="flex justify-center pt-[5px]">
                    -&gt;
                  </AntCol>
                  <AntCol span={11}>
                    <AntForm.Item
                      label="Assign"
                      {...field}
                      name={[name, "dataCategory"]}
                      rules={[
                        {
                          required: true,
                          message: "Data category is required",
                        },
                      ]}
                    >
                      <DataCategorySelect
                        selectedTaxonomies={[]}
                        variant="outlined"
                        placeholder="Select a data category"
                        autoFocus={false}
                        allowClear
                      />
                    </AntForm.Item>
                  </AntCol>
                  <AntCol span={1} className="mt-[7.25px]">
                    {idx === fields.length - 1 ? (
                      <AntButton
                        onClick={() => add()}
                        icon={<Icons.Add />}
                        aria-label="Add new rule"
                      />
                    ) : (
                      <AntButton
                        onClick={() => remove(name)}
                        icon={<Icons.TrashCan />}
                        aria-label="Remove rule"
                      />
                    )}
                  </AntCol>
                </AntRow>
              ))}
              <AntForm.ErrorList errors={errors} />
              {/* TODO: make this work with the modal's built-in submit button */}
              <AntForm.Item label={null}>
                <AntButton
                  type="primary"
                  htmlType="submit"
                  loading={createIsLoading || updateIsLoading}
                >
                  Submit
                </AntButton>
              </AntForm.Item>
            </>
          )}
        </AntForm.List>
      </AntForm>
    </>
  );
};

export default SharedMonitorConfigForm;
