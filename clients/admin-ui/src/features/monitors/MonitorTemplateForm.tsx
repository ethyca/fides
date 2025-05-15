import { AntButton, AntCol, AntForm, AntInput, AntRow, Icons } from "fidesui";

import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
import {
  MonitorTemplateCreate,
  MonitorTemplateFormValues,
  MonitorTemplateResponse,
} from "~/features/monitors/types";
import {
  useMockCreateMonitorTemplateQuery,
  useMockUpdateMonitorTemplateQuery,
} from "~/features/monitors/useMockGetMonitorTemplatesQuery";

const DEFAULT_INITIAL_VALUES: Partial<MonitorTemplateFormValues> = {
  rules: [],
};

const MonitorTemplateForm = ({
  monitor,
}: {
  monitor?: MonitorTemplateResponse;
}) => {
  const [form] = AntForm.useForm<MonitorTemplateFormValues>();

  const { trigger: createMonitorTemplate, isLoading: createIsLoading } =
    useMockCreateMonitorTemplateQuery();
  const { trigger: updateMonitorTemplate, isLoading: updateIsLoading } =
    useMockUpdateMonitorTemplateQuery();

  const transformMonitorResponseToFormValues = (
    response: MonitorTemplateResponse,
  ): MonitorTemplateFormValues => {
    return {
      ...response,
      rules: response.regexMap.map(([regex, dataCategory]) => ({
        regex,
        dataCategory,
      })),
    };
  };

  const transformFormValuesToPayload = (
    values: MonitorTemplateFormValues,
  ): MonitorTemplateCreate => {
    return {
      name: values.name,
      rules: values.rules.map(({ regex, dataCategory }) => [
        regex,
        dataCategory,
      ]),
    };
  };

  const onSubmit = (values: MonitorTemplateFormValues) => {
    const payload = transformFormValuesToPayload(values);
    if (monitor) {
      updateMonitorTemplate({ ...payload, id: monitor.id });
    } else {
      createMonitorTemplate(payload);
    }
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
