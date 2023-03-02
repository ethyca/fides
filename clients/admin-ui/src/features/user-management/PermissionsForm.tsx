import { Checkbox, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";

import { USER_PRIVILEGES } from "~/constants";

const requiredPermission = "privacy-request:read";

const defaultInitialValues = {
  scopes: [requiredPermission],
};

const PermissionsForm = () => (
  <Formik
    onSubmit={() => {}}
    initialValues={defaultInitialValues}
    //   validationSchema={validationSchema}
  >
    {({ setFieldValue, values }) => (
      <Form>
        <Stack spacing={[1, 5]} direction="column">
          {USER_PRIVILEGES.map((policy) => {
            const isChecked = values.scopes.indexOf(policy.scope) >= 0;
            return (
              <Checkbox
                colorScheme="purple"
                key={policy.privilege}
                onChange={() => {
                  if (!isChecked) {
                    setFieldValue(`scopes`, [...values.scopes, policy.scope]);
                  } else {
                    setFieldValue(
                      "scopes",
                      values.scopes.filter((scope) => scope !== policy.scope)
                    );
                  }
                }}
                id={`scopes-${policy.privilege}`}
                name="scopes"
                isChecked={isChecked}
                value={
                  policy.scope === requiredPermission ? undefined : policy.scope
                }
                isDisabled={policy.scope === requiredPermission}
                isReadOnly={policy.scope === requiredPermission}
              >
                {policy.privilege}
              </Checkbox>
            );
          })}
        </Stack>
      </Form>
    )}
  </Formik>
);

export default PermissionsForm;
