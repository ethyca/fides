import { Divider, Stack, Text } from "@fidesui/react";
import { useFormikContext } from "formik";
import { ReactNode } from "react";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import {
  CustomCheckbox,
  CustomRadioGroup,
  CustomSwitch,
} from "~/features/common/form/inputs";
import { selectGppSettings } from "~/features/privacy-requests";
import { GPPSettings, GPPUSApproach } from "~/types/api";

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
  const { values } = useFormikContext<{ gpp: GPPSettings }>();
  const showMspa = !!values.gpp.us_approach;

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
                ]}
              />
            </Section>
            {showMspa ? (
              <Section title="MSPA">
                <CustomCheckbox
                  name="gpp.mspa_covered_transactions"
                  label="All transactions covered by MSPA"
                  tooltip="When selected, the Fides CMP will communicate to downstream vendors that all preferences are covered under the MSPA."
                />
                <CustomSwitch
                  label="Enable MSPA service provider mode"
                  name="gpp.mspa_service_provider_mode"
                  variant="switchFirst"
                  tooltip="Enable opt-out option mode if you engage or may engage in the sales or sharing of personal information, or process any information for the purpose of targeted advertising."
                  isDisabled={values.gpp.mspa_opt_out_option_mode}
                />
                <CustomSwitch
                  label="Enable MSPA opt-out option mode"
                  name="gpp.mspa_opt_out_option_mode"
                  variant="switchFirst"
                  tooltip="Enable service provider mode if you do not engage in any sales or sharing of personal information."
                  isDisabled={values.gpp.mspa_service_provider_mode}
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
                tooltip="TODO"
              />
            </Section>
          </>
        ) : null}
      </Stack>
    </SettingsBox>
  );
};

export default GppConfiguration;
