import {Box, HStack, IconButton, TrashCanSolidIcon, useDisclosure} from "@fidesui/react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import Restrict from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import React from "react";
import DeleteUserModal from "user-management/DeleteUserModal";
import {User} from "user-management/types";
import NewPasswordModal from "./NewPasswordModal";
import UpdatePasswordModal from "./UpdatePasswordModal";
import {selectActiveUserId} from "./user-management.slice";

interface PasswordManagementProps {
  user: User;
  isNewUser: boolean
}

const PasswordManagement: React.FC<PasswordManagementProps> = ({ user, isNewUser }) => {
  const activeUserId = useAppSelector(selectActiveUserId);
  const loggedInUser = useAppSelector(selectUser);
  const deleteModal = useDisclosure();

  // if (!activeUserId) {
  //   return (
  //     <CustomTextInput
  //       name="password"
  //       label="Password"
  //       placeholder="********"
  //       type="password"
  //       tooltip="Password must contain at least 8 characters, 1 number, 1 capital letter, 1 lowercase letter, and at least 1 symbol."
  //     />
  //   );
  // }
  const isOwnProfile = loggedInUser ? loggedInUser.id === activeUserId : false;

  return (
      <Box>
      {activeUserId ?
              <HStack>
                  {isOwnProfile ? <UpdatePasswordModal id={activeUserId}/> : null}
                  <Restrict scopes={[ScopeRegistryEnum.USER_PASSWORD_RESET]}>
                      <NewPasswordModal id={activeUserId}/>
                  </Restrict>

                  {!isNewUser && user
                      ?
                      <Box>
                          <IconButton
                              aria-label="delete"
                              icon={<TrashCanSolidIcon />}
                              size="xs"
                              onClick={deleteModal.onOpen}
                              data-testid="delete-user-btn"
                          />
                          <DeleteUserModal user={user} {...deleteModal} />
                      </Box>
                      : null
                  }
              </HStack>
              : null
      }
      </Box>
  );
};

export default PasswordManagement;
