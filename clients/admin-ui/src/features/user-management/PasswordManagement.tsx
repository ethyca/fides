import { HStack } from "@fidesui/react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { CustomTextInput } from "~/features/common/form/inputs";
import Restrict from "~/features/common/Restrict";
import { ScopeRegistry } from "~/types/api";

import NewPasswordModal from "./NewPasswordModal";
import UpdatePasswordModal from "./UpdatePasswordModal";

interface Props {
  profileId?: string;
}
const PasswordManagement = ({ profileId }: Props) => {
  const isNewUser = profileId == null;
  const currentUser = useAppSelector(selectUser);

  const isOwnProfile = currentUser ? currentUser.id === profileId : false;

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

  return (
    <HStack>
      {isOwnProfile ? <UpdatePasswordModal id={profileId} /> : null}
      <Restrict scopes={[ScopeRegistry.USER_PASSWORD_RESET]}>
        <NewPasswordModal id={profileId} />
      </Restrict>
    </HStack>
  );
};

export default PasswordManagement;
