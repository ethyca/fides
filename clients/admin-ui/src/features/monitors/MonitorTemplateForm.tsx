import {
  AntButton,
  AntCol,
  AntForm,
  AntInput,
  AntRow,
  Icons,
  useToast,
} from "fidesui";

import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useCreateSharedMonitorConfigMutation,
  useUpdateSharedMonitorConfigMutation,
} from "~/features/monitors/shared-monitor-config.slice";
import { MonitorTemplateFormValues } from "~/features/monitors/types";
import { SharedMonitorConfig } from "~/types/api/models/SharedMonitorConfig";
import { isErrorResult, RTKResult } from "~/types/errors";

const DEFAULT_INITIAL_VALUES: Partial<MonitorTemplateFormValues> = {
  rules: [],
};

const MonitorTemplateForm = ({
  monitor,
}: {
  monitor?: SharedMonitorConfig;
}) => {
  const [form] = AntForm.useForm<MonitorTemplateFormValues>();
  const toast = useToast();

  const [createMonitorTemplate, { isLoading: createIsLoading }] =
    useCreateSharedMonitorConfigMutation();
  const [updateMonitorTemplate, { isLoading: updateIsLoading }] =
    useUpdateSharedMonitorConfigMutation();

  const transformMonitorResponseToFormValues = (
    response: SharedMonitorConfig,
  ): MonitorTemplateFormValues => {
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
    values: MonitorTemplateFormValues,
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

  const onSubmit = async (values: MonitorTemplateFormValues) => {
    const payload = transformFormValuesToPayload(values);
    let result;
    if (monitor) {
      result = await updateMonitorTemplate({ ...payload, id: monitor.id });
    } else {
      result = await createMonitorTemplate(payload);
    }
    handleResult(result, !monitor);
  };

  return (
    <AntForm
      name="monitor-template"
      layout="vertical"
      form={form}
      onFinish={onSubmit}
      className="mt-4"
      initialValues={
        monitor
          ? transformMonitorResponseToFormValues(monitor)
          : DEFAULT_INITIAL_VALUES
      }
      validateTrigger={["onBlur", "onChange"]}
    >
      <AntRow>
        <AntCol span={17}>
          <AntForm.Item
            label="Config name"
            name="name"
            layout="horizontal"
            rules={[{ required: true, message: "Config name is required" }]}
          >
            <AntInput autoFocus />
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
            {fields.map(({ key, name, ...field }) => (
              <AntRow gutter={16} key={key}>
                <AntCol span={8}>
                  <AntForm.Item
                    label="On match"
                    layout="horizontal"
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
                <AntCol span={8}>
                  <AntForm.Item
                    label="Assign"
                    layout="horizontal"
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
                {fields.length > 1 && (
                  <AntCol span={1}>
                    <AntButton
                      onClick={() => remove(name)}
                      icon={<Icons.TrashCan />}
                    />
                  </AntCol>
                )}
              </AntRow>
            ))}
            <AntForm.Item>
              <AntButton onClick={() => add()}>Add</AntButton>
            </AntForm.Item>
            <AntForm.ErrorList errors={errors} />
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
  );
};

export default MonitorTemplateForm;
