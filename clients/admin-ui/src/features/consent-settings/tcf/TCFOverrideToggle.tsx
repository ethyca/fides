import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/query";
import {
  AntSpace as Space,
  AntSwitch as Switch,
  AntSwitchProps as SwitchProps,
  ConfirmationModal,
  Text,
  useToast,
} from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
import { errorToastParams } from "~/features/common/toast";
import { isErrorResult } from "~/types/errors";

import { InfoTooltip } from "../../common/InfoTooltip";
import { usePatchConfigurationSettingsMutation } from "../../config-settings/config-settings.slice";
import {
  useGetHealthQuery,
  useGetTcfPurposeOverridesQuery,
  usePatchTcfPurposeOverridesMutation,
} from "../../plus/plus.slice";

export const TCFOverrideToggle = ({
  defaultChecked,
  onChange,
  ...props
}: Omit<SwitchProps, "onChange" | "checked"> & {
  onChange?: (checked: boolean) => void;
}) => {
  const toast = useToast();

  const [isChecked, setIsChecked] = useState(defaultChecked);
  const [isModalOpen, setIsModalOpen] = useState(false);
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
      onChange?.(checked);
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          `An unexpected error occurred while saving vendor override settings. Please try again.`,
        );
        onChange?.(false);
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

  const handleBeforeChange = (checked: boolean) => {
    if (checked) {
      setIsChecked(checked);
      handleOverrideOnChange(checked);
    } else {
      setIsModalOpen(true);
    }
  };

  const handleConfirmDisable = () => {
    setIsChecked(false);
    handleOverrideOnChange(false);
    setIsModalOpen(false);
  };

  return (
    <>
      <Space direction="vertical" size="small">
        <Text>Configure overrides for TCF related purposes.</Text>
        <Space size="small">
          <Switch
            size="small"
            disabled={isPatchConfigSettingsLoading}
            loading={isPatchConfigSettingsLoading}
            {...props}
            checked={isChecked}
            defaultChecked={defaultChecked}
            onClick={handleBeforeChange}
            data-testid="tcf-override-toggle"
          />
          <Text>Override vendor purposes</Text>
          <InfoTooltip label="Toggle on if you want to globally change any flexible legal bases or remove TCF purposes from your CMP" />
        </Space>
      </Space>
      <ConfirmationModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleConfirmDisable}
        title="Disable Vendor Overrides"
        message="Are you sure you want to disable vendor overrides? Clicking 'Continue' will immediately remove any custom configurations you have set for TCF purposes for all experiences."
      />
    </>
  );
};
