import { Checkbox, Stack } from "@fidesui/react";
import { Form, Formik } from "formik";

import { RoleRegistry, UserPermissionsEdit } from "~/types/api";

import { useUpdateUserPermissionsMutation } from "./user-management.slice";

const defaultInitialValues = {
  roles: [] as RoleRegistry[],
};

const ROLES = [
  { label: "Owner", key: RoleRegistry.ADMIN },
  // TODO: update once the backend has this
  //   { label: "Contributor", key: RoleRegistry.ADMIN },
  { label: "Viewer", key: RoleRegistry.VIEWER },
  {
    label: "Viewer & Approver",
    key: RoleRegistry.VIEWER_AND_PRIVACY_REQUEST_MANAGER,
  },
  { label: "Approver", key: RoleRegistry.PRIVACY_REQUEST_MANAGER },
];

type FormValues = typeof defaultInitialValues;

const PermissionsForm = ({
  user_id,
  roles,
  scopes,
}: UserPermissionsEdit & { user_id: string }) => {
  const initialValues = roles ? { roles } : defaultInitialValues;
  const [updateUserPermissionMutationTrigger] =
    useUpdateUserPermissionsMutation();
  const handleSubmit = async (values: FormValues) => {
    // TODO: error handling and whatnot
    await updateUserPermissionMutationTrigger({
      user_id,
      // Scopes are not editable in the UI, but make sure we retain whatever scopes
      // the user might've already had
      payload: { scopes, roles: values.roles },
    });
  };

  return (
    <Formik onSubmit={handleSubmit} initialValues={initialValues}>
      {({ setFieldValue, values }) => (
        <Form>
          <Stack spacing={[1, 5]} direction="column">
            {ROLES.map((role) => {
              const isChecked = values.roles.indexOf(role.key) >= 0;
              return (
                <Checkbox
                  colorScheme="purple"
                  key={role.key}
                  onChange={() => {
                    if (!isChecked) {
                      setFieldValue(`roles`, [...values.roles, role.key]);
                    } else {
                      setFieldValue(
                        "roles",
                        values.roles.filter((r) => r !== role.key)
                      );
                    }
                  }}
                  id={`roles-${role.key}`}
                  name="roles"
                  isChecked={isChecked}
                  value={role.key}
                >
                  {role.label}
                </Checkbox>
              );
            })}
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default PermissionsForm;
