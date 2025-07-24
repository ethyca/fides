import { Divider, Stack, Text } from "fidesui";
import { useFormikContext } from "formik";
import { ReactNode } from "react";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import ControlledRadioGroup from "~/features/common/form/ControlledRadioGroup";
import { CustomCheckbox, CustomSwitch } from "~/features/common/form/inputs";
import { selectGppSettings } from "~/features/config-settings/config-settings.slice";
import { GPPUSApproach, PrivacyExperienceGPPSettings } from "~/types/api";

import FrameworkStatus from "./FrameworkStatus";
import SettingsBox from "./SettingsBox";

const Section = ({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) => (
  <Stack spacing={3} mb={3} data-testid={`section-${title}`}>
    <Text fontSize="sm" fontWeight="bold" lineHeight={5} color="gray.700">
      {title}
    </Text>
    {children}
  </Stack>
);

const GppConfiguration = () => {
  const { tcf: isTcfEnabled } = useFeatures();
  const gppSettings = useAppSelector(selectGppSettings);
  const isEnabled = !!gppSettings.enabled;
  const { values, setFieldValue } = useFormikContext<{
    gpp: PrivacyExperienceGPPSettings;
  }>();
  const showMspa = !!values.gpp.us_approach;

  return (
    <SettingsBox title="Global Privacy Platform">
      <Stack spacing={6}>
        <FrameworkStatus name="GPP" enabled={isEnabled} />
        {isEnabled ? (
          <>
            <Section title="GPP U.S.">
              <ControlledRadioGroup
                name="gpp.us_approach"
                layout="stacked"
                defaultFirstSelected={false}
                options={[
                  {
                    label: "Enable U.S. National",
                    value: GPPUSApproach.NATIONAL,
                    tooltip:
                      "When US National is selected, Fides will present the same privacy notices to all consumers located anywhere in the United States.",
                  },
                  {
                    label: "Enable U.S. State-by-State",
                    value: GPPUSApproach.STATE,
                    tooltip:
                      "When state-by-state is selected, Fides will only present consent to consumers and save their preferences if they are located in a state that is supported by the GPP. The consent options presented to consumers will vary depending on the regulations in each state.",
                  },
                  {
                    label: "Enable US National and State-by-State notices",
                    value: GPPUSApproach.ALL,
                    tooltip:
                      "When enabled, Fides can be configured to serve the National and U.S. state notices. This mode is intended to provide consent coverage to U.S. states with new privacy laws where GPP support lags behind the effective date of state laws.",
                  },
                ]}
              />
            </Section>
            {showMspa ? (
              <Section title="MSPA">
                <CustomCheckbox
                  name="gpp.mspa_covered_transactions"
                  label="All transactions covered by MSPA"
                  tooltip="When selected, the Fides CMP will communicate to downstream vendors that all preferences are covered under the MSPA."
                  onChange={(checked) => {
                    if (!checked) {
                      setFieldValue("gpp.mspa_service_provider_mode", false);
                      setFieldValue("gpp.mspa_opt_out_option_mode", false);
                    }
                  }}
                />
                <CustomSwitch
                  label="Enable MSPA service provider mode"
                  name="gpp.mspa_service_provider_mode"
                  variant="switchFirst"
                  tooltip="Enable service provider mode if you do not engage in any sales or sharing of personal information."
                  isDisabled={
                    !!values.gpp.mspa_opt_out_option_mode ||
                    !values.gpp.mspa_covered_transactions
                  }
                />
                <CustomSwitch
                  label="Enable MSPA opt-out option mode"
                  name="gpp.mspa_opt_out_option_mode"
                  variant="switchFirst"
                  tooltip="Enable opt-out option mode if you engage or may engage in the sales or sharing of personal information, or process any information for the purpose of targeted advertising."
                  isDisabled={
                    !!values.gpp.mspa_service_provider_mode ||
                    !values.gpp.mspa_covered_transactions
                  }
                />
              </Section>
            ) : null}
          </>
        ) : null}
        {isTcfEnabled ? (
          <>
            <Divider color="gray.200" />
            <Section title="GPP Europe">
              <Text fontSize="sm" fontWeight="medium">
                Configure TCF string for Global Privacy Platform
              </Text>
              <CustomSwitch
                label="Enable TC string"
                name="gpp.enable_tcfeu_string"
                variant="switchFirst"
                tooltip="When enabled, the GPP API will include a TCF EU consent string for users who are in regions where TCF applies."
              />
            </Section>
          </>
        ) : null}
      </Stack>
    </SettingsBox>
  );
};

export default GppConfiguration;
