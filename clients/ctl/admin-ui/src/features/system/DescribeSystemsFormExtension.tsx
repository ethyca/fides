import { Box, FormLabel, Stack } from "@fidesui/react";

import { YesNoOptions } from "~/features/common/constants";
import { COUNTRY_OPTIONS } from "~/features/common/countries";
import {
  CustomMultiSelect,
  CustomRadioGroup,
  CustomSelect,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import QuestionTooltip from "~/features/common/QuestionTooltip";
import type { FormValues } from "~/features/system/DescribeSystemStep";
import { DataResponsibilityTitle } from "~/types/api";

const dataResponsibilityOptions = enumToOptions(DataResponsibilityTitle);

const DescribeSystemsFormExtension = ({ values }: { values: FormValues }) => (
  <>
    <CustomSelect
      label="Data responsibility title"
      name="data_responsibility_title"
      options={dataResponsibilityOptions}
      tooltip="An attribute to describe the role of responsibility over the personal data, used when exporting to a data map"
    />
    <CustomTextInput
      label="Administrating department"
      name="administrating_department"
      tooltip="An optional value to identify the owning department or group of the system within your organization"
    />
    <CustomMultiSelect
      name="third_country_transfers"
      label="Geographic location"
      tooltip="An optional array to identify any third countries where data is transited to. For consistency purposes, these fields are required to follow the Alpha-3 code set in ISO 3166-1"
      isSearchable
      options={COUNTRY_OPTIONS}
    />
    <Box>
      <Box display="flex" alignItems="center" mb={4}>
        <FormLabel mb={0}>Joint controller</FormLabel>
        <QuestionTooltip label="Contact information if a Joint Controller exists" />
      </Box>
      <Stack ml={8}>
        <CustomTextInput label="Name" name="joint_controller.name" />
        <CustomTextInput label="Address" name="joint_controller.address" />
        <CustomTextInput label="Email" name="joint_controller.email" />
        <CustomTextInput label="Phone" name="joint_controller.phone" />
      </Stack>
    </Box>
    <Box>
      <Box display="flex" alignItems="center" mb={4}>
        <FormLabel mb={0}>Data protection impact assessment</FormLabel>
        <QuestionTooltip label="Contains information in regard to the data protection impact assessment exported on a data map or Record of Processing Activities (RoPA)." />
      </Box>
      <Stack ml={8}>
        <CustomRadioGroup
          name="data_protection_impact_assessment.is_required"
          label="Is required"
          options={YesNoOptions}
        />
        {values.data_protection_impact_assessment.is_required === "true" ? (
          <>
            <CustomTextInput
              label="Progress"
              name="data_protection_impact_assessment.progress"
              tooltip="The optional status of a Data Protection Impact Assessment. Returned on an exported data map or RoPA."
            />
            <CustomTextInput
              label="Link"
              name="data_protection_impact_assessment.link"
              tooltip="The optional link to the Data Protection Impact Assessment. Returned on an exported data map or RoPA."
            />
          </>
        ) : null}
      </Stack>
    </Box>
  </>
);

export default DescribeSystemsFormExtension;
