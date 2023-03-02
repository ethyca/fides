import { useState } from "react";

import DataTabs, { type TabData } from "~/features/common/DataTabs";

import { isErrorResult } from "../common/helpers";
import PermissionsForm from "./PermissionsForm";
import UserForm, {
  type FormValues,
  type Props as UserFormProps,
} from "./UserForm";

const UserManagementTabs = ({
  onSubmit,
  initialValues,
  ...props
}: UserFormProps) => {
  const [isNewUser, setIsNewUser] = useState(!initialValues);

  const handleSubmit = async (values: FormValues) => {
    const result = await onSubmit(values);
    if (!isErrorResult(result)) {
      setIsNewUser(false);
    }
    return result;
  };

  const tabs: TabData[] = [
    {
      label: "Profile",
      content: (
        <UserForm
          onSubmit={handleSubmit}
          initialValues={initialValues}
          {...props}
        />
      ),
    },
    {
      label: "Permissions",
      content: <PermissionsForm />,
      isDisabled: isNewUser,
    },
  ];

  return <DataTabs data={tabs} />;
};

export default UserManagementTabs;
