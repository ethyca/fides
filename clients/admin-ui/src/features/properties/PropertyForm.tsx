import { AntButton as Button, Box, Flex } from "fidesui";
import { Form, Formik, useFormikContext } from "formik";
import { useRouter } from "next/router";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import FormSection from "~/features/common/form/FormSection";
import {
  CustomClipboardCopy,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { enumToOptions } from "~/features/common/helpers";
import { PROPERTIES_ROUTE } from "~/features/common/nav/routes";
import ScrollableList from "~/features/common/ScrollableList";
import {
  selectAllExperienceConfigs,
  selectPage,
  selectPageSize,
  useGetAllExperienceConfigsQuery,
} from "~/features/privacy-experience/privacy-experience.slice";
import {
  MinimalMessagingTemplate,
  MinimalPrivacyExperienceConfig,
  Property,
  PropertyType,
} from "~/types/api";

import { ControlledSelect } from "../common/form/ControlledSelect";
import DeletePropertyModal from "./DeletePropertyModal";

interface Props {
  property?: Property;
  handleSubmit: (values: FormValues) => Promise<void>;
}

export interface FormValues {
  id?: string | null;
  name: string;
  type: PropertyType;
  messaging_templates?: Array<MinimalMessagingTemplate> | null;
  experiences: Array<MinimalPrivacyExperienceConfig>;
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
        baseTestId="experience"
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
    () =>
      property || {
        name: "",
        type: PropertyType.WEBSITE,
        experiences: [],
        messaging_templates: [],
        paths: [],
      },
    [property],
  );

  return (
    <Formik
      enableReinitialize
      initialValues={initialValues}
      onSubmit={handleSubmit}
    >
      {({ dirty, isValid, isSubmitting }) => (
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
              <ControlledSelect
                isRequired
                label="Type"
                name="type"
                options={enumToOptions(PropertyType)}
                layout="stacked"
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
          <Flex justifyContent="space-between" width="100%" paddingTop={2}>
            {property && (
              <DeletePropertyModal
                property={property}
                triggerComponent={
                  <Button
                    data-testid="delete-property-button"
                    loading={false}
                    className="mr-3"
                  >
                    Delete
                  </Button>
                }
              />
            )}
            <Flex justifyContent="right" width="100%" paddingTop={2}>
              <Button onClick={handleCancel} loading={false} className="mr-3">
                Cancel
              </Button>
              <Button
                htmlType="submit"
                type="primary"
                disabled={isSubmitting || !dirty || !isValid}
                loading={isSubmitting}
              >
                Save
              </Button>
            </Flex>
          </Flex>
        </Form>
      )}
    </Formik>
  );
};

export default PropertyForm;
