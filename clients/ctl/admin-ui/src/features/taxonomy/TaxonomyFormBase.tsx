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

import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult, parseError } from "~/features/common/helpers";
import { successToastParams } from "~/features/common/toast";
import { RTKErrorResult } from "~/types/errors";

import TaxonomyEntityTag from "./TaxonomyEntityTag";
import { Labels, TaxonomyEntity, TaxonomyRTKResult } from "./types";

export type FormValues = Partial<TaxonomyEntity> &
  Pick<TaxonomyEntity, "fides_key">;

interface Props {
  entity: TaxonomyEntity;
  labels: Labels;
  onCancel: () => void;
  onEdit: (entity: TaxonomyEntity) => TaxonomyRTKResult;
  extraFormFields?: ReactNode;
  initialValues: FormValues;
}
const EditTaxonomyForm = ({
  entity,
  labels,
  onCancel,
  onEdit,
  extraFormFields,
  initialValues,
}: Props) => {
  const toast = useToast();
  const [formError, setFormError] = useState<string | null>(null);

  const handleError = (error: RTKErrorResult["error"]) => {
    const parsedError = parseError(error);
    setFormError(parsedError.message);
  };

  const handleSubmit = async (newValues: FormValues) => {
    setFormError(null);
    // parent_key and fides_keys are immutable
    const payload = {
      ...newValues,
      parent_key: entity.parent_key,
      fides_key: entity.fides_key,
    };
    const result = await onEdit(payload);
    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      toast(successToastParams("Taxonomy successfully updated"));
    }
  };

  return (
    <Stack pl={6} spacing={6} data-testid="edit-taxonomy-form">
      <Heading size="md" textTransform="capitalize">
        Modify {labels.fides_key}
      </Heading>

      <Formik
        initialValues={initialValues}
        onSubmit={handleSubmit}
        enableReinitialize
      >
        {({ dirty }) => (
          <Form>
            <Stack mb={6}>
              <Grid templateColumns="1fr 3fr">
                <FormLabel>{labels.fides_key}</FormLabel>
                <Box>
                  <TaxonomyEntityTag name={entity.fides_key} />
                </Box>
              </Grid>
              <CustomTextInput name="name" label={labels.name} />
              <CustomTextArea name="description" label={labels.description} />
              <CustomTextInput
                name="parent_key"
                label={labels.parent_key}
                disabled
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
                disabled={!dirty}
              >
                Update entity
              </Button>
            </ButtonGroup>
          </Form>
        )}
      </Formik>
    </Stack>
  );
};

export default EditTaxonomyForm;
