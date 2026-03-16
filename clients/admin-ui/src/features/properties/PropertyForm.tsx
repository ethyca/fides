import { Button, ChakraBox as Box, ChakraFlex as Flex, Switch } from "fidesui";
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
  PrivacyCenterConfig,
  Property,
  PropertyType,
} from "~/types/api";

import { ControlledSelect } from "../common/form/ControlledSelect";
import DeletePropertyModal from "./DeletePropertyModal";
import { DEFAULT_PRIVACY_CENTER_CONFIG } from "./privacy-center/helpers";
import PathsFieldArray from "./privacy-center/PathsFieldArray";
import PrivacyCenterConfigForm from "./privacy-center/PrivacyCenterConfigForm";

interface Props {
  property?: Property;
  handleSubmit: (values: PropertyFormValues) => Promise<void>;
  rightPanel?: React.ReactNode;
}

export interface PropertyFormValues {
  id?: string | null;
  name: string;
  type: PropertyType;
  messaging_templates?: Array<MinimalMessagingTemplate> | null;
  experiences: Array<MinimalPrivacyExperienceConfig>;
  privacy_center_config?: PrivacyCenterConfig | null;
  paths: Array<string>;
}

/** @deprecated Use PropertyFormValues */
export type FormValues = PropertyFormValues;

const ExperiencesFormSection = () => {
  const page = useAppSelector(selectPage);
  const pageSize = useAppSelector(selectPageSize);
  useGetAllExperienceConfigsQuery({
    page,
    size: pageSize,
  });
  const experienceConfigs = useAppSelector(selectAllExperienceConfigs);
  const { values, setFieldValue } = useFormikContext<PropertyFormValues>();

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

const PrivacyCenterToggleSection = () => {
  const { values, setFieldValue } = useFormikContext<PropertyFormValues>();
  const hasConfig =
    values.privacy_center_config !== null &&
    values.privacy_center_config !== undefined;

  return (
    <Box py={3}>
      <FormSection title="Privacy Center">
        <Flex alignItems="center" gap={3}>
          <Switch
            checked={hasConfig}
            onChange={(checked) => {
              if (checked) {
                setFieldValue(
                  "privacy_center_config",
                  DEFAULT_PRIVACY_CENTER_CONFIG,
                );
              } else {
                setFieldValue("privacy_center_config", null);
              }
            }}
            data-testid="privacy-center-toggle"
          />
          <Box fontSize="sm" color="gray.700">
            {hasConfig ? "Privacy Center enabled" : "Enable Privacy Center"}
          </Box>
        </Flex>
      </FormSection>
    </Box>
  );
};

const PropertyForm = ({ property, handleSubmit, rightPanel }: Props) => {
  const router = useRouter();

  const handleCancel = () => {
    router.push(PROPERTIES_ROUTE);
  };

  const initialValues: PropertyFormValues = useMemo(
    () =>
      property
        ? {
            id: property.id,
            name: property.name,
            type: property.type,
            messaging_templates: property.messaging_templates,
            experiences: property.experiences,
            privacy_center_config: property.privacy_center_config ?? null,
            paths: property.paths ?? [],
          }
        : {
            name: "",
            type: PropertyType.WEBSITE,
            experiences: [],
            messaging_templates: [],
            privacy_center_config: null,
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
        <Flex gap={6} alignItems="flex-start">
          <Form
            style={{
              paddingTop: "12px",
              paddingBottom: "12px",
              flex: rightPanel ? "0 0 480px" : "1",
              minWidth: 0,
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
            <Box py={3}>
              <FormSection title="Paths">
                <PathsFieldArray />
              </FormSection>
            </Box>
            <PrivacyCenterToggleSection />
            <PrivacyCenterConfigForm />
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
          {rightPanel && (
            <Box
              flex="1"
              minWidth={0}
              position="sticky"
              top={4}
              style={{ paddingTop: "24px" }}
            >
              {rightPanel}
            </Box>
          )}
        </Flex>
      )}
    </Formik>
  );
};

export default PropertyForm;
