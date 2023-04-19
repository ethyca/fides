import { Box, Text } from "@fidesui/react";
import { useFormikContext } from "formik";
import { useEffect, useMemo } from "react";

import FormSection from "~/features/common/form/FormSection";
import { CustomSelect, CustomSwitch } from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import {
  ConsentMechanism,
  EnforcementLevel,
  PrivacyNoticeCreation,
} from "~/types/api";

import { ENFORCEMENT_LEVEL_MAP, MECHANISM_MAP } from "./constants";

const CONSENT_MECHANISM_OPTIONS = enumToOptions(ConsentMechanism).map(
  (opt) => ({
    label: MECHANISM_MAP.get(opt.label) || opt.label,
    value: opt.value,
  })
);

const ENFORCEMENT_OPTIONS = enumToOptions(EnforcementLevel).map((opt) => ({
  label: ENFORCEMENT_LEVEL_MAP.get(opt.label) || opt.label,
  value: opt.value,
}));

const ConsentMechanismForm = () => {
  const { values, setFieldValue } = useFormikContext<PrivacyNoticeCreation>();

  const isNoticeOnly = useMemo(
    () => values.consent_mechanism === ConsentMechanism.NOTICE_ONLY,
    [values.consent_mechanism]
  );

  // Handle the special case where, if the consent mechanism is "Notice only", some fields
  // become disabled
  useEffect(() => {
    if (isNoticeOnly) {
      setFieldValue("enforcement_level", EnforcementLevel.NOT_APPLICABLE);
      setFieldValue("has_gpc_flag", false);
    }
  }, [isNoticeOnly, setFieldValue]);

  return (
    <FormSection title="Consent mechanism">
      <CustomSelect
        label="If this use of data requires consent, you can specify the method of consent here."
        name="consent_mechanism"
        options={CONSENT_MECHANISM_OPTIONS}
        variant="stacked"
      />
      <CustomSelect
        label="Select the enforcement level for this consent mechanism"
        name="enforcement_level"
        options={ENFORCEMENT_OPTIONS}
        variant="stacked"
        isDisabled={isNoticeOnly}
      />
      <Box>
        <Text fontSize="sm" fontWeight="medium" mb={2}>
          Configure whether this notice conforms to the Global Privacy Control.
        </Text>
        <CustomSwitch
          label="GPC Enabled"
          name="has_gpc_flag"
          variant="condensed"
          isDisabled={isNoticeOnly}
        />
      </Box>
    </FormSection>
  );
};

export default ConsentMechanismForm;
