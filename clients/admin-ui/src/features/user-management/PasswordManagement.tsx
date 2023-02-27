import { HStack } from "@fidesui/react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { CustomTextInput } from "~/features/common/form/inputs";

import NewPasswordModal from "./NewPasswordModal";
import UpdatePasswordModal from "./UpdatePasswordModal";
import { useGetUserPermissionsQuery } from "./user-management.slice";

interface Props {
  profileId?: string;
}
const PasswordManagement = ({ profileId }: Props) => {
  const isNewUser = profileId == null;
  const currentUser = useAppSelector(selectUser);
  const { data: userPermissions } = useGetUserPermissionsQuery(
    currentUser?.id ?? ""
  );

  const isOwnProfile = currentUser ? currentUser.id === profileId : false;
  const canForceResetPassword = userPermissions?.scopes
    ? userPermissions.scopes.includes("user:password-reset")
    : false;

  if (isNewUser) {
    return (
      <CustomTextInput
        name="password"
        label="Password"
        placeholder="********"
        type="password"
        tooltip="Password must contain at least 8 characters, 1 number, 1 capital letter, 1 lowercase letter, and at least 1 symbol."
      />
    );
  }

  if (!profileId) {
    return null;
  }

  if (!isOwnProfile && !canForceResetPassword) {
    return null;
  }

  return (
    <HStack>
      {isOwnProfile ? <UpdatePasswordModal id={profileId} /> : null}
      {canForceResetPassword ? <NewPasswordModal id={profileId} /> : null}
    </HStack>
  );
};

export default PasswordManagement;
