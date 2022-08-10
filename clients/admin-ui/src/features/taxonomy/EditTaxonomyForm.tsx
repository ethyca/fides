import { Button, ButtonGroup, Heading, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";

import { CustomTextArea, CustomTextInput } from "../common/form/inputs";
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
        <Form>
          <Stack mb={6}>
            <CustomTextInput name="name" label="Name" />
            <CustomTextArea name="description" label="Description" />
            <CustomTextInput name="parent_key" label="Parent" />
          </Stack>

          <ButtonGroup size="sm">
            <Button
              data-testid="cancel-btn"
              variant="outline"
              onClick={onCancel}
            >
              Cancel
            </Button>
            <Button data-testid="update-btn" variant="primary" type="submit">
              Update entity
            </Button>
          </ButtonGroup>
        </Form>
      </Formik>
    </Stack>
  );
};

export default EditTaxonomyForm;
