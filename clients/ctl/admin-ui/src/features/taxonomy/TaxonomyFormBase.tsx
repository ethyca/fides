import {
  Box,
  Button,
  ButtonGroup,
  FormLabel,
  Grid,
  Heading,
  Stack,
  Text,
  useToast,
} from "@fidesui/react";
import { Form, Formik } from "formik";
import { ReactNode, useState } from "react";
import * as Yup from "yup";

import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult, parseError } from "~/features/common/helpers";
import { successToastParams } from "~/features/common/toast";
import { RTKErrorResult } from "~/types/errors";

import TaxonomyEntityTag from "./TaxonomyEntityTag";
import { Labels, TaxonomyEntity, TaxonomyRTKResult } from "./types";

export type FormValues = Partial<TaxonomyEntity> &
  Pick<TaxonomyEntity, "fides_key">;

interface Props {
  labels: Labels;
  onCancel: () => void;
  onSubmit: (entity: TaxonomyEntity) => TaxonomyRTKResult;
  extraFormFields?: ReactNode;
  initialValues: FormValues;
  isCreate?: boolean;
}
const EditTaxonomyForm = ({
  labels,
  onCancel,
  onSubmit,
  extraFormFields,
  initialValues,
  isCreate = false,
}: Props) => {
  const toast = useToast();
  const [formError, setFormError] = useState<string | null>(null);
  const ValidationSchema = Yup.object().shape({
    fides_key: Yup.string().required().label(labels.fides_key),
  });

  const handleError = (error: RTKErrorResult["error"]) => {
    const parsedError = parseError(error);
    setFormError(parsedError.message);
  };

  const handleSubmit = async (newValues: FormValues) => {
    setFormError(null);
    // parent_key and fides_keys are immutable
    // parent_key also needs to be undefined, not an empty string, if there is no parent element
    const payload = isCreate
      ? {
          ...newValues,
          parent_key:
            newValues.parent_key === "" ? undefined : newValues.parent_key,
        }
      : {
          ...newValues,
          parent_key:
            initialValues.parent_key === ""
              ? undefined
              : initialValues.parent_key,
          fides_key: initialValues.fides_key,
        };
    const result = await onSubmit(payload);
    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      toast(
        successToastParams(
          `Taxonomy successfully ${isCreate ? "created" : "updated"}`
        )
      );
    }
  };

  return (
    <Stack pl={6} spacing={6} data-testid="edit-taxonomy-form">
      <Heading size="md" textTransform="capitalize">
        {isCreate ? "Create" : "Modify"} {labels.fides_key}
      </Heading>

      <Formik
        initialValues={initialValues}
        onSubmit={handleSubmit}
        validationSchema={ValidationSchema}
        enableReinitialize
      >
        {({ dirty }) => (
          <Form>
            <Stack mb={6}>
              {isCreate ? (
                <CustomTextInput name="fides_key" label={labels.fides_key} />
              ) : (
                <Grid templateColumns="1fr 3fr">
                  <FormLabel>{labels.fides_key}</FormLabel>
                  <Box>
                    <TaxonomyEntityTag name={initialValues.fides_key} />
                  </Box>
                </Grid>
              )}
              <CustomTextInput name="name" label={labels.name} />
              <CustomTextArea name="description" label={labels.description} />
              <CustomTextInput
                name="parent_key"
                label={labels.parent_key}
                disabled={!isCreate}
              />
              {extraFormFields}
            </Stack>

            {formError ? (
              <Text color="red" mb={2} data-testid="taxonomy-form-error">
                {formError}
              </Text>
            ) : null}

            <ButtonGroup size="sm">
              <Button
                data-testid="cancel-btn"
                variant="outline"
                onClick={onCancel}
              >
                Cancel
              </Button>
              <Button
                data-testid="update-btn"
                variant="primary"
                type="submit"
                disabled={!isCreate && !dirty}
              >
                {isCreate ? "Create entity" : "Update entity"}
              </Button>
            </ButtonGroup>
          </Form>
        )}
      </Formik>
    </Stack>
  );
};

export default EditTaxonomyForm;
