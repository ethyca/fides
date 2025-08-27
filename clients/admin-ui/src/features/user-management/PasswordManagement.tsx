import { Box, HStack } from "fidesui";
import React from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import Restrict from "~/features/common/Restrict";
import { RoleRegistryEnum, ScopeRegistryEnum } from "~/types/api";

import NewPasswordModal from "./NewPasswordModal";
import UpdatePasswordModal from "./UpdatePasswordModal";
import {
  selectActiveUserId,
  useGetUserPermissionsQuery,
} from "./user-management.slice";

const PasswordManagement = () => {
  const activeUserId = useAppSelector(selectActiveUserId);
  const loggedInUser = useAppSelector(selectUser);
  const isOwnProfile = loggedInUser ? loggedInUser.id === activeUserId : false;

  const { data: userPermissions } = useGetUserPermissionsQuery(
    activeUserId ?? "",
    {
      skip: !activeUserId,
    },
  );

  // Check if the current user is an external respondent
  const isExternalRespondent = Boolean(
    userPermissions?.roles?.includes(RoleRegistryEnum.EXTERNAL_RESPONDENT),
  );

  // External respondents cannot access password management
  if (isExternalRespondent) {
    return null;
  }

  return (
    <Box>
      {activeUserId ? (
        <HStack>
          {isOwnProfile ? <UpdatePasswordModal id={activeUserId} /> : null}
          <Restrict scopes={[ScopeRegistryEnum.USER_PASSWORD_RESET]}>
            <NewPasswordModal id={activeUserId} />
          </Restrict>
        </HStack>
      ) : null}
    </Box>
  );
};

export default PasswordManagement;
