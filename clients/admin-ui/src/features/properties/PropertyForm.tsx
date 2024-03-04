import { Box, Button, Flex } from "@fidesui/react";
import { Form, Formik, useFormikContext } from "formik";
import { useRouter } from "next/router";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import FormSection from "~/features/common/form/FormSection";
import {
  CustomClipboardCopy,
  CustomSelect,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import { PROPERTIES_ROUTE } from "~/features/common/nav/v2/routes";
import ScrollableList from "~/features/common/ScrollableList";
import {
  selectAllExperienceConfigs,
  selectPage,
  selectPageSize,
  useGetAllExperienceConfigsQuery,
} from "~/features/privacy-experience/privacy-experience.slice";
import { MinimalPrivacyExperience, Property, PropertyType } from "~/types/api";

interface Props {
  property?: Property;
  handleSubmit: (values: FormValues) => Promise<void>;
}

export interface FormValues {
  id: string;
  name: string;
  type: string;
  experiences: Array<MinimalPrivacyExperience>;
}

const ExperiencesFormSection = () => {
  const page = useAppSelector(selectPage);
  const pageSize = useAppSelector(selectPageSize);
  useGetAllExperienceConfigsQuery({
    page,
    size: pageSize,
  });
  const experienceConfigs = useAppSelector(selectAllExperienceConfigs);
  const { values, setFieldValue } = useFormikContext<FormValues>();

  return (
    <FormSection title="Experiences">
      <ScrollableList
        addButtonLabel="Add experience"
        idField="id"
        nameField="name"
        allItems={experienceConfigs.map((exp) => ({
          id: exp.id,
          name: exp.name,
        }))}
        values={values.experiences ?? []}
        setValues={(newValues) => setFieldValue("experiences", newValues)}
        draggable
      />
    </FormSection>
  );
};

const PropertyForm = ({ property, handleSubmit }: Props) => {
  const router = useRouter();

  const handleCancel = () => {
    router.push(PROPERTIES_ROUTE);
  };

  const initialValues = useMemo(
    () => property || { name: "", type: "", experiences: [] },
    [property]
  );

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      onSubmit={handleSubmit}
    >
      <Form
        style={{
          paddingTop: "12px",
          paddingBottom: "12px",
        }}
      >
        <Box py={3}>
          <FormSection title="Property details">
            <CustomTextInput
              isRequired
              label="Property name"
              name="name"
              tooltip="Unique name to identify this property"
              variant="stacked"
            />
            <CustomSelect
              isRequired
              label="Type"
              name="type"
              options={enumToOptions(PropertyType)}
              variant="stacked"
            />
          </FormSection>
        </Box>
        <Box py={3}>
          <ExperiencesFormSection />
        </Box>
        {property && (
          <Box py={3}>
            <FormSection title="Advanced settings">
              <CustomClipboardCopy
                label="Property ID"
                name="id"
                tooltip="Automatically generated unique ID for this property, used for developer configurations"
                variant="stacked"
                readOnly
              />
            </FormSection>
          </Box>
        )}
        <Flex justifyContent="right" width="100%" paddingTop={2}>
          <Button
            size="sm"
            type="submit"
            variant="outline"
            isLoading={false}
            mr={3}
            onClick={handleCancel}
          >
            Cancel
          </Button>
          <Button
            size="sm"
            type="submit"
            colorScheme="primary"
            isLoading={false}
          >
            Save
          </Button>
        </Flex>
      </Form>
    </Formik>
  );
};

export default PropertyForm;
