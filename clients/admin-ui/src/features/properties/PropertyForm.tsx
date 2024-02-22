import { Box, Button, Flex, useToast } from "@fidesui/react";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import { useMemo } from "react";

import FormSection from "~/features/common/form/FormSection";
import { Property } from "~/types/api";

import {
  CustomClipboardCopy,
  CustomSelect,
  CustomTextInput,
} from "../common/form/inputs";
import { PROPERTIES_ROUTE } from "../common/nav/v2/routes";
import { errorToastParams, successToastParams } from "../common/toast";
import { useCreatePropertyMutation } from "./property.slice";

interface Props {
  property?: Property;
}

export interface FormValues {
  name: string;
  type: string;
}

const PropertyForm = ({ property }: Props) => {
  const toast = useToast();
  const router = useRouter();
  const [createProperty] = useCreatePropertyMutation();

  const initialValues = useMemo(
    () => property || { name: "", type: "" },
    [property]
  );

  const handleSubmit = async (values: FormValues) => {
    try {
      const prop = await createProperty(values).unwrap();
      toast(successToastParams(`Property ${values.name} created successfully`));
      router.push(`${PROPERTIES_ROUTE}/${prop.key}`);
    } catch (error) {
      toast(errorToastParams(`Failed to create property.`));
    }
  };

  return (
    <Formik initialValues={initialValues} onSubmit={handleSubmit}>
      {() => (
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
                options={[
                  { value: "website", label: "Website" },
                  { value: "other", label: "Other" },
                ]}
                variant="stacked"
              />
            </FormSection>
          </Box>
          {property && (
            <Box py={3}>
              <FormSection title="Advanced settings">
                <CustomClipboardCopy
                  label="Property key"
                  name="key"
                  variant="stacked"
                  readOnly
                />
              </FormSection>
            </Box>
          )}
          <Flex justifyContent="right" width="100%" paddingTop={2}>
            {!property && (
              <Button
                size="sm"
                type="submit"
                colorScheme="primary"
                isLoading={false}
              >
                Save
              </Button>
            )}
          </Flex>
        </Form>
      )}
    </Formik>
  );
};

export default PropertyForm;
