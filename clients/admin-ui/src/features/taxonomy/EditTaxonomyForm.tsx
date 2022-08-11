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
import { useState } from "react";

import { isErrorResult, parseError } from "~/features/common/helpers";
import { RTKErrorResult } from "~/types/errors";

import { CustomTextArea, CustomTextInput } from "../common/form/inputs";
import { successToastParams } from "../common/toast";
import TaxonomyEntityTag from "./TaxonomyEntityTag";
import { Labels, TaxonomyEntity, TaxonomyRTKResult } from "./types";

type FormValues = Partial<TaxonomyEntity> & Pick<TaxonomyEntity, "fides_key">;

interface Props {
  entity: TaxonomyEntity;
  labels: Labels;
  onCancel: () => void;
  onEdit: (entity: TaxonomyEntity) => TaxonomyRTKResult;
}
const EditTaxonomyForm = ({ entity, labels, onCancel, onEdit }: Props) => {
  const toast = useToast();
  const initialValues: FormValues = {
    fides_key: entity.fides_key,
    name: entity.name ?? "",
    description: entity.description ?? "",
    parent_key: entity.parent_key ?? "",
  };
  const [formError, setFormError] = useState<string | null>(null);

  const handleError = (error: RTKErrorResult["error"]) => {
    const parsedError = parseError(error);
    setFormError(parsedError.message);
  };

  const handleSubmit = async (newValues: FormValues) => {
    setFormError(null);
    const result = await onEdit(newValues);
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
            </Stack>

            {formError ? (
              <Text color="red" mb={2}>
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
