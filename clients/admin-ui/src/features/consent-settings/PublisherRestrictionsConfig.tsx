import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  AntButton as Button,
  AntSelect as Select,
  AntSpace as Space,
  AntSwitch as Switch,
  Skeleton,
  Text,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import { useState } from "react";
import * as Yup from "yup";

import { CustomTextInput } from "~/features/common/form/inputs";
import { getErrorMessage } from "~/features/common/helpers";
import FormModal from "~/features/common/modals/FormModal";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useCreateTCFConfigurationMutation,
  useGetTCFConfigurationsQuery,
} from "~/features/consent-settings/tcf-config.slice";
import { isErrorResult } from "~/types/errors";

import DocsLink from "../common/DocsLink";
import QuestionTooltip from "../common/QuestionTooltip";
import { usePatchConfigurationSettingsMutation } from "../config-settings/config-settings.slice";
import {
  useGetHealthQuery,
  useGetTcfPurposeOverridesQuery,
  usePatchTcfPurposeOverridesMutation,
} from "../plus/plus.slice";
import SettingsBox from "./SettingsBox";

const PUBLISHER_RESTRICTIONS_DOCS_URL =
  "https://ethyca.com/docs/tutorials/consent-management/consent-management-configuration/configure-tcf#vendor-overrides";

interface PublisherRestrictionsConfigProps {
  isTCFOverrideEnabled: boolean;
}

interface CreateTCFConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const ValidationSchema = Yup.object().shape({
  name: Yup.string().required().label("Name"),
});

const CreateTCFConfigModal = ({
  isOpen,
  onClose,
}: CreateTCFConfigModalProps) => {
  const toast = useToast();
  const [createTCFConfiguration] = useCreateTCFConfigurationMutation();

  const handleSubmit = async (values: { name: string }) => {
    const result = await createTCFConfiguration({ name: values.name });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(successToastParams("Successfully created TCF configuration"));
      onClose();
    }
  };

  return (
    <FormModal
      title="Create a new TCF configuration"
      isOpen={isOpen}
      onClose={onClose}
    >
      <Formik
        initialValues={{ name: "" }}
        onSubmit={handleSubmit}
        validationSchema={ValidationSchema}
      >
        {({ isValid, dirty }) => (
          <Form>
            <Space direction="vertical" size="small" className="w-full">
              <Text>
                TCF configurations allow you to define unique sets of publisher
                restrictions. These configurations can be added to privacy
                experiences.
              </Text>
              <CustomTextInput
                id="name"
                name="name"
                label="Name"
                isRequired
                variant="stacked"
              />
              <Space className="w-full justify-end pt-6">
                <Button onClick={onClose}>Cancel</Button>
                <Button
                  type="primary"
                  htmlType="submit"
                  disabled={!isValid || !dirty}
                >
                  Save
                </Button>
              </Space>
            </Space>
          </Form>
        )}
      </Formik>
    </FormModal>
  );
};

export const PublisherRestrictionsConfig = ({
  isTCFOverrideEnabled,
}: PublisherRestrictionsConfigProps) => {
  const [showTcfOverrideConfig, setShowTcfOverrideConfig] =
    useState<boolean>(isTCFOverrideEnabled);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [selectedTCFConfigId, setSelectedTCFConfigId] = useState<string | null>(
    null,
  );
  const { data: tcfConfigurations, isLoading: isTcfConfigurationsLoading } =
    useGetTCFConfigurationsQuery(
      { page: 1, size: 50 },
      { skip: !isTCFOverrideEnabled },
    );

  const toast = useToast();

  const { isLoading: isHealthCheckLoading } = useGetHealthQuery();
  const [
    patchConfigSettingsTrigger,
    { isLoading: isPatchConfigSettingsLoading },
  ] = usePatchConfigurationSettingsMutation();
  const [patchTcfPurposeOverridesTrigger] =
    usePatchTcfPurposeOverridesMutation();
  const { data: tcfPurposeOverrides } = useGetTcfPurposeOverridesQuery(
    undefined,
    {
      skip: isHealthCheckLoading,
    },
  );

  const handleOverrideOnChange = async (checked: boolean) => {
    const handleResult = (
      result:
        | { data: object }
        | { error: FetchBaseQueryError | SerializedError },
    ) => {
      toast.closeAll();
      setShowTcfOverrideConfig(checked);
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          `An unexpected error occurred while saving vendor override settings. Please try again.`,
        );
        setShowTcfOverrideConfig(false);
        toast(errorToastParams(errorMsg));
      }
    };

    const result = await patchConfigSettingsTrigger({
      consent: {
        override_vendor_purposes: checked,
      },
    });

    if (checked && tcfPurposeOverrides) {
      await patchTcfPurposeOverridesTrigger(
        tcfPurposeOverrides.map((po) => ({
          ...po,
          is_included: true,
          required_legal_basis: undefined,
        })),
      );
    }

    handleResult(result);
  };

  return (
    <SettingsBox title="Publisher restrictions" fontSize="sm">
      <Space direction="vertical" size="small">
        <Text>Configure overrides for TCF related purposes.</Text>
        {/* eslint-disable-next-line no-nested-ternary */}
        {isTcfConfigurationsLoading ? (
          <>
            <Skeleton height="20px" />
            <Skeleton height="20px" />
          </>
        ) : tcfConfigurations?.items?.length ? (
          <>
            <Space size="small">
              <Switch
                size="small"
                defaultChecked={showTcfOverrideConfig}
                onChange={handleOverrideOnChange}
                disabled={isPatchConfigSettingsLoading}
              />
              <Text>Override vendor purposes</Text>
              <QuestionTooltip label="Toggle on if you want to globally change any flexible legal bases or remove TCF purposes from your CMP" />
            </Space>
            {showTcfOverrideConfig && (
              <>
                <Text>
                  The table below allows you to adjust which TCF purposes you
                  allow as part of your user facing notices and business
                  activities.
                </Text>
                <Text>
                  To configure this section, select a TCF purpose to edit the
                  restriction type and vendors.{" "}
                  <DocsLink href={PUBLISHER_RESTRICTIONS_DOCS_URL}>
                    Learn more about publisher restrictions
                  </DocsLink>{" "}
                  in our docs.
                </Text>
                <Select
                  className="w-auto"
                  defaultValue={tcfConfigurations?.items?.[0]?.id}
                  options={
                    tcfConfigurations?.items?.map((c) => ({
                      label: c.name,
                      value: c.id,
                    })) || []
                  }
                  onChange={(value) => setSelectedTCFConfigId(value)}
                />
              </>
            )}
          </>
        ) : (
          <>
            <Text>
              To define custom publisher restrictions select &quot;create
              configuration&quot; below.{" "}
              <DocsLink href={PUBLISHER_RESTRICTIONS_DOCS_URL}>
                Learn more about publisher restrictions
              </DocsLink>{" "}
              in our docs.
            </Text>
            <Button onClick={() => setIsCreateModalOpen(true)}>
              Create configuration +
            </Button>
          </>
        )}
      </Space>
      <CreateTCFConfigModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      />
    </SettingsBox>
  );
};
