import {
  Box,
  Button,
  ButtonGroup,
  FormLabel,
  Grid,
  Heading,
  Stack,
} from "@fidesui/react";
import { Form, Formik } from "formik";

import { CustomTextArea, CustomTextInput } from "../common/form/inputs";
import DataCategoryTag from "./DataCategoryTag";
import { Labels, TaxonomyEntity } from "./types";

type FormValues = TaxonomyEntity;

interface Props {
  entity: TaxonomyEntity;
  labels: Labels;
  onCancel: () => void;
  onEdit: (entity: TaxonomyEntity) => void;
}
const EditTaxonomyForm = ({ entity, labels, onCancel, onEdit }: Props) => {
  const initialValues: FormValues = {
    fides_key: entity.fides_key,
    name: entity.name ?? "",
    description: entity.description ?? "",
    parent_key: entity.parent_key ?? "",
  };

  const handleSubmit = (newValues: FormValues) => {
    console.log({ newValues });
    onEdit(newValues);
  };

  return (
    <Stack pl={6} spacing={6}>
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
                  <DataCategoryTag name={entity.fides_key} size="sm" />
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
