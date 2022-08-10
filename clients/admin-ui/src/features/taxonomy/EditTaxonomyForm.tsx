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
import { TaxonomyEntity } from "./types";

type FormValues = Partial<TaxonomyEntity>;

interface Props {
  entity: TaxonomyEntity;
  onCancel: () => void;
}
const EditTaxonomyForm = ({ entity, onCancel }: Props) => {
  const initialValues: FormValues = {
    name: entity.name ?? "",
    description: entity.description ?? "",
    parent_key: entity.parent_key ?? "",
  };

  const handleSubmit = (newValues: FormValues) => {
    console.log({ newValues });
  };

  return (
    <Stack pl={6} spacing={6}>
      <Heading size="md">Modify {entity.name}</Heading>

      <Formik
        initialValues={initialValues}
        onSubmit={handleSubmit}
        enableReinitialize
      >
        {({ dirty }) => (
          <Form>
            <Stack mb={6}>
              <Grid templateColumns="1fr 3fr">
                <FormLabel>Entity</FormLabel>
                <Box>
                  <DataCategoryTag name={entity.fides_key} size="sm" />
                </Box>
              </Grid>
              <CustomTextInput name="name" label="Name" />
              <CustomTextArea name="description" label="Description" />
              <CustomTextInput name="parent_key" label="Parent" disabled />
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
