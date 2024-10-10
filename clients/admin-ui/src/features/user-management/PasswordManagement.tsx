import { Box, HStack } from "fidesui";
import React from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import Restrict from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import NewPasswordModal from "./NewPasswordModal";
import UpdatePasswordModal from "./UpdatePasswordModal";
import { selectActiveUser, selectActiveUserId } from "./user-management.slice";

const PasswordManagement = () => {
  const activeUserId = useAppSelector(selectActiveUserId);
  const activeUser = useAppSelector(selectActiveUser);
  const loggedInUser = useAppSelector(selectUser);
  const isOwnProfile = loggedInUser ? loggedInUser.id === activeUserId : false;

  return (
    <Box>
      {activeUserId ? (
        <HStack>
          {isOwnProfile ? <UpdatePasswordModal id={activeUserId} /> : null}
          <Restrict scopes={[ScopeRegistryEnum.USER_PASSWORD_RESET]}>
            <NewPasswordModal
              id={activeUserId}
              username={activeUser?.username ?? ""}
            />
          </Restrict>
        </HStack>
      ) : null}
    </Box>
  );
};

export default PasswordManagement;
