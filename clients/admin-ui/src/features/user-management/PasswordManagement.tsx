import { HStack } from "@fidesui/react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { CustomTextInput } from "~/features/common/form/inputs";
import Restrict from "~/features/common/Restrict";
import { ScopeRegistry } from "~/types/api";

import NewPasswordModal from "./NewPasswordModal";
import UpdatePasswordModal from "./UpdatePasswordModal";
import { selectActiveUserId } from "./user-management.slice";

const PasswordManagement = () => {
  const activeUserId = useAppSelector(selectActiveUserId);
  const loggedInUser = useAppSelector(selectUser);

  if (!activeUserId) {
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
  const isOwnProfile = loggedInUser ? loggedInUser.id === activeUserId : false;

  return (
    <HStack>
      {isOwnProfile ? <UpdatePasswordModal id={activeUserId} /> : null}
      <Restrict scopes={[ScopeRegistry.USER_PASSWORD_RESET]}>
        <NewPasswordModal id={activeUserId} />
      </Restrict>
    </HStack>
  );
};

export default PasswordManagement;
