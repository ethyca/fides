import {
  AntButton,
  Box,
  FormLabel,
  Grid,
  Heading,
  Input,
  Stack,
  Text,
  useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import { ReactNode, useState } from "react";
import * as Yup from "yup";

import { CustomTextArea, CustomTextInput } from "~/features/common/form/inputs";
import { isErrorResult, parseError } from "~/features/common/helpers";
import { successToastParams } from "~/features/common/toast";
import { RTKResult } from "~/features/common/types";
import { RTKErrorResult } from "~/types/errors";

import { parentKeyFromFidesKey } from "./helpers";
import TaxonomyEntityTag from "./TaxonomyEntityTag";
import { FormValues, Labels, TaxonomyEntity } from "./types";

interface Props {
  labels: Labels;
  onCancel: () => void;
  onSubmit: (
    initialValues: FormValues,
    newValues: FormValues,
  ) => RTKResult<TaxonomyEntity>;
  renderExtraFormFields?: (entity: FormValues) => ReactNode;
  initialValues: FormValues;
}
const TaxonomyFormBase = ({
  labels,
  onCancel,
  onSubmit,
  renderExtraFormFields,
  initialValues,
}: Props) => {
  const toast = useToast();
  const [formError, setFormError] = useState<string | null>(null);
  const ValidationSchema = Yup.object().shape({
    fides_key: Yup.string().required().label(labels.fides_key),
  });
  const isCreate = initialValues.fides_key === "";

  const handleError = (error: RTKErrorResult["error"]) => {
    const parsedError = parseError(error);
    setFormError(parsedError.message);
  };

  const handleSubmit = async (newValues: FormValues) => {
    setFormError(null);

    const result = await onSubmit(initialValues, newValues);

    if (isErrorResult(result)) {
      handleError(result.error);
    } else {
      toast(
        successToastParams(
          `Taxonomy successfully ${isCreate ? "created" : "updated"}`,
        ),
      );
      if (isCreate) {
        onCancel();
      }
    }
  };

  return (
    <Stack
      pl={6}
      spacing={6}
      data-testid={`${isCreate ? "create" : "edit"}-taxonomy-form`}
    >
      <Heading size="md" textTransform="capitalize" data-testid="form-heading">
        {isCreate ? "Create" : "Modify"} {labels.fides_key}
      </Heading>

      <Formik
        initialValues={initialValues}
        onSubmit={handleSubmit}
        validationSchema={ValidationSchema}
        enableReinitialize
      >
        {({ dirty, values }) => (
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
              {labels.parent_key &&
                (isCreate ? (
                  <Grid templateColumns="1fr 3fr">
                    <FormLabel>{labels.parent_key}</FormLabel>
                    <Box mr="2">
                      <Input
                        data-testid="input-parent_key"
                        disabled
                        value={parentKeyFromFidesKey(values.fides_key)}
                        size="sm"
                      />
                    </Box>
                  </Grid>
                ) : (
                  <CustomTextInput
                    name="parent_key"
                    label={labels.parent_key}
                    disabled={!isCreate}
                  />
                ))}
              {renderExtraFormFields ? renderExtraFormFields(values) : null}
            </Stack>

            {formError ? (
              <Text color="red" mb={2} data-testid="taxonomy-form-error">
                {formError}
              </Text>
            ) : null}

            <div>
              <AntButton data-testid="cancel-btn" onClick={onCancel}>
                Cancel
              </AntButton>
              <AntButton
                data-testid="submit-btn"
                type="primary"
                htmlType="submit"
                disabled={!isCreate && !dirty}
              >
                {isCreate ? "Create entity" : "Update entity"}
              </AntButton>
            </div>
          </Form>
        )}
      </Formik>
    </Stack>
  );
};

export default TaxonomyFormBase;
