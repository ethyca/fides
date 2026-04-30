import {
  Button,
  Flex,
  Form,
  Icons,
  Input,
  Spin,
  Typography,
  useMessage,
} from "fidesui";
import { isEqual } from "lodash";
import type { NextPage } from "next";
import { useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import DocsLink from "~/features/common/DocsLink";
import FormSection from "~/features/common/form/FormSection";
import { corsOriginRules } from "~/features/common/form/validation";
import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import {
  CORSOrigins,
  selectApplicationConfig,
  selectCORSOrigins,
  useGetConfigurationSettingsQuery,
  usePutConfigurationSettingsMutation,
} from "~/features/config-settings/config-settings.slice";
import { PlusApplicationConfig } from "~/types/api";
import { RTKErrorResult } from "~/types/errors/api";

type FormValues = CORSOrigins;

const CORSConfigurationPage: NextPage = () => {
  const { isLoading: isLoadingGetQuery } = useGetConfigurationSettingsQuery({
    api_set: true,
  });
  const { isLoading: isLoadingConfigSetQuery } =
    useGetConfigurationSettingsQuery({
      api_set: false,
    });
  const currentSettings = useAppSelector(selectCORSOrigins);
  const apiSettings = currentSettings.apiSet;
  const configSettings = currentSettings.configSet;
  const hasConfigSettings: boolean = !!(
    configSettings.cors_origins?.length || configSettings.cors_origin_regex
  );
  const applicationConfig = useAppSelector(selectApplicationConfig());
  const [putConfigSettingsTrigger, { isLoading: isLoadingPutMutation }] =
    usePutConfigurationSettingsMutation();

  const message = useMessage();
  const [form] = Form.useForm<FormValues>();
  const allValues = Form.useWatch([], form);
  const [submittable, setSubmittable] = useState(false);
  const [baseline, setBaseline] = useState(apiSettings);

  useEffect(() => {
    setBaseline(apiSettings);
  }, [apiSettings]);

  useEffect(() => {
    form
      .validateFields({ validateOnly: true })
      .then(() => setSubmittable(true))
      .catch(() => setSubmittable(false));
  }, [form, allValues]);

  const isDirty = useMemo(
    () => !isEqual(form.getFieldsValue(true), baseline),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [allValues, baseline],
  );

  const handleSubmit = async (values: FormValues) => {
    const payloadOrigins =
      values.cors_origins && values.cors_origins.length > 0
        ? values.cors_origins
        : undefined;

    const payload: PlusApplicationConfig = {
      ...applicationConfig,
      security: {
        cors_origins: payloadOrigins,
      },
    };

    try {
      await putConfigSettingsTrigger(payload).unwrap();
      message.success("Domains saved successfully");
      setBaseline({ cors_origins: values.cors_origins ?? undefined });
    } catch (error) {
      message.error(
        getErrorMessage(
          error as RTKErrorResult["error"],
          "An unexpected error occurred while saving domains. Please try again.",
        ),
      );
    }
  };

  return (
    <Layout title="Domains">
      <div data-testid="management-domains">
        <PageHeader heading="Domains" />
        <div className="max-w-[600px]">
          <Typography.Paragraph className="pb-6 text-sm">
            For Fides to work on your website(s), each of your domains must be
            listed below. You can add and remove domains at any time up to the
            quantity included in your license. For more information on managing
            domains{" "}
            <DocsLink href="https://fid.es/domain-configuration">
              read here
            </DocsLink>
            .
          </Typography.Paragraph>
          <FormSection
            data-testid="api-set-domains-form"
            title="Organization domains"
            tooltip="Fides uses these domains to enforce cross-origin resource sharing (CORS), a browser-based security standard. Each domain must be a valid URL (e.g. https://example.com) without any wildcards '*' or paths '/blog'"
          >
            {isLoadingGetQuery || isLoadingPutMutation ? (
              <Spin rootClassName="my-24" />
            ) : (
              <Form
                form={form}
                initialValues={apiSettings}
                onFinish={handleSubmit}
                key={JSON.stringify(apiSettings)}
              >
                <Form.List name="cors_origins">
                  {(fields, { add, remove }) => (
                    <Flex vertical>
                      {fields.map((field) => (
                        <Flex className="my-3" key={field.key}>
                          <Form.Item
                            name={field.name}
                            className="mb-0 grow"
                            rules={corsOriginRules}
                          >
                            <Input
                              placeholder="https://subdomain.example.com:9090"
                              data-testid={`input-cors_origins[${field.name}]`}
                            />
                          </Form.Item>

                          <Button
                            aria-label="delete-domain"
                            className="z-[2] ml-4"
                            icon={<Icons.TrashCan />}
                            onClick={() => {
                              remove(field.name);
                            }}
                          />
                        </Flex>
                      ))}

                      <Flex justify="center" className="mt-3">
                        <Button
                          aria-label="add-domain"
                          className="w-full"
                          onClick={() => {
                            add("");
                          }}
                        >
                          Add domain
                        </Button>
                      </Flex>
                    </Flex>
                  )}
                </Form.List>

                <div className="mt-6">
                  <Button
                    htmlType="submit"
                    type="primary"
                    disabled={isLoadingPutMutation || !isDirty || !submittable}
                    loading={isLoadingPutMutation}
                    data-testid="save-btn"
                  >
                    Save
                  </Button>
                </div>
              </Form>
            )}
          </FormSection>
        </div>
        <div className="my-3 max-w-[600px]">
          <FormSection
            data-testid="config-set-domains-form"
            title="Advanced settings"
            tooltip="These domains are configured by an administrator with access to Fides security settings and can support more advanced options such as wildcards and regex."
          >
            {isLoadingConfigSetQuery ? (
              <Spin rootClassName="my-24" />
            ) : (
              <Flex vertical>
                {configSettings.cors_origins!.map((origin, index) => (
                  <Input
                    data-testid={`input-config_cors_origins[${index}]`}
                    // eslint-disable-next-line react/no-array-index-key
                    key={index}
                    className="my-3"
                    value={origin}
                    disabled
                  />
                ))}
                {configSettings.cors_origin_regex ? (
                  <Input
                    data-testid="input-config_cors_origin_regex"
                    key="cors_origin_regex"
                    className="my-3"
                    value={configSettings.cors_origin_regex}
                    disabled
                  />
                ) : undefined}
                {!hasConfigSettings ? (
                  <Typography.Text type="secondary" className="text-xs">
                    No advanced domain settings configured.
                  </Typography.Text>
                ) : undefined}
              </Flex>
            )}
          </FormSection>
        </div>
      </div>
    </Layout>
  );
};
export default CORSConfigurationPage;
