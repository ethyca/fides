import { Stack, Text } from "@fidesui/react";
import { useFormikContext } from "formik";
import { ReactNode } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  CustomCheckbox,
  CustomRadioGroup,
  CustomSwitch,
} from "~/features/common/form/inputs";
import { selectGppSettings } from "~/features/privacy-requests";
import {
  fidesplus__config__gpp_settings__GPPUSApproach as GPPUSApproach,
  GPPSettings,
} from "~/types/api";

import FrameworkStatus from "./FrameworkStatus";
import SettingsBox from "./SettingsBox";

const Section = ({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) => (
  <Stack spacing={3} mb={3}>
    <Text fontSize="sm" fontWeight="bold" lineHeight={5} color="gray.700">
      {title}
    </Text>
    {children}
  </Stack>
);

const GppConfiguration = () => {
  const gppSettings = useAppSelector(selectGppSettings);
  const isEnabled = !!gppSettings.enabled;
  const { values } = useFormikContext<{ gpp: GPPSettings }>();

  return (
    <SettingsBox title="Global Privacy Platform">
      <Stack spacing={6}>
        <FrameworkStatus name="GPP" enabled={isEnabled} />
        {isEnabled ? (
          <>
            <Section title="GPP U.S.">
              <CustomRadioGroup
                name="gpp.us_approach"
                variant="stacked"
                options={[
                  {
                    label: "Enable U.S. National",
                    value: GPPUSApproach.NATIONAL,
                    tooltip: "TODO",
                  },
                  {
                    label: "Enable U.S. State-by-State",
                    value: GPPUSApproach.STATE,
                    tooltip: "TODO",
                  },
                ]}
              />
            </Section>
            <Section title="MSPA">
              <CustomCheckbox
                name="gpp.mspa_covered_transactions"
                label="All transactions covered by MSPA"
                tooltip="TODO"
              />
              <CustomSwitch
                label="Enable MSPA service provider mode"
                name="gpp.mspa_service_provider_mode"
                variant="switchFirst"
                tooltip="TODO"
                isDisabled={values.gpp.mspa_opt_out_option_mode}
              />
              <CustomSwitch
                label="Enable MSPA opt-out option mode"
                name="gpp.mspa_opt_out_option_mode"
                variant="switchFirst"
                tooltip="TODO"
                isDisabled={values.gpp.mspa_service_provider_mode}
              />
            </Section>
          </>
        ) : null}
      </Stack>
    </SettingsBox>
  );
};

export default GppConfiguration;
