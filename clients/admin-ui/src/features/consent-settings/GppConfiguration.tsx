import { Button, Stack, Text } from "@fidesui/react";
import { Form, Formik } from "formik";
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
    <Text fontSize="md" fontWeight="bold" lineHeight={5} color="gray.700">
      {title}
    </Text>
    {children}
  </Stack>
);

const GppConfiguration = () => {
  const gppSettings = useAppSelector(selectGppSettings);
  // const initialValues = {
  //   // camel case for FE only values, will be transformed back in handleSubmit
  //   isUsNational: gppSettings.us_approach === GPPUSApproach.NATIONAL,
  //   isUsState: gppSettings.us_approach === GPPUSApproach.STATE,
  //   // snake case to stay consistent with backend
  //   mspa_covered_transactions: gppSettings.mspa_covered_transactions ?? false,
  //   mspa_opt_out_option_mode: gppSettings.mspa_opt_out_option_mode ?? false,
  //   mspa_service_provider_mode: gppSettings.mspa_service_provider_mode ?? false,
  // };

  const handleSubmit = (values: GPPSettings) => {
    console.log({ values });
  };

  return (
    <Formik
      onSubmit={handleSubmit}
      initialValues={gppSettings}
      enableReinitialize
    >
      <Form>
        <SettingsBox title="Global Privacy Platform">
          <Stack spacing={6}>
            <FrameworkStatus name="GPP" enabled={!!gppSettings.enabled} />
            <Section title="GPP U.S.">
              <CustomRadioGroup
                name="us_approach"
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
                name="mspa_covered_transactions"
                label="All transactions covered by MSPA"
                tooltip="TODO"
              />
              <CustomSwitch
                label="Enable MSPA service provider mode"
                name="mspa_service_provider_mode"
                variant="switchFirst"
                tooltip="TODO"
              />
              <CustomSwitch
                label="Enable MSPA opt-out option mode"
                name="mspa_opt_out_option_mode"
                variant="switchFirst"
                tooltip="TODO"
              />
            </Section>
            <Button
              type="submit"
              size="sm"
              colorScheme="primary"
              width="fit-content"
            >
              Save
            </Button>
          </Stack>
        </SettingsBox>
      </Form>
    </Formik>
  );
};

export default GppConfiguration;
