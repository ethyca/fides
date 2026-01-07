import {
  AntAlert as Alert,
  AntButton as Button,
  AntModal as Modal,
  Box,
  Text,
} from "fidesui";
import React, { useState } from "react";
import { useSelector } from "react-redux";
import UserManagementTabs from "user-management/UserManagementTabs";

import { selectUser } from "~/features/auth";
import { useAlert } from "~/features/common/hooks/useAlert";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import { useAPIHelper } from "../common/hooks";
import PageHeader from "../common/PageHeader";
import { User } from "./types";
import {
  useEditUserMutation,
  useReinviteUserMutation,
} from "./user-management.slice";
import { FormValues } from "./UserForm";

const useUserForm = (profile: User) => {
  const currentUser = useSelector(selectUser);
  const [editUser] = useEditUserMutation();

  const initialValues: FormValues = {
    username: profile.username ?? "",
    email_address: profile.email_address ?? "",
    first_name: profile.first_name ?? "",
    last_name: profile.last_name ?? "",
    password: "",
    password_login_enabled: Boolean(profile.password_login_enabled),
  };

  const handleSubmit = async (values: FormValues) => {
    const userBody = {
      ...values,
      id: profile.id,
    };
    return editUser(userBody);
  };

  const isOwnProfile = currentUser ? currentUser.id === profile.id : false;
  const hasUserUpdatePermission = useHasPermission([
    ScopeRegistryEnum.USER_UPDATE,
  ]);
  const canUpdateUser = isOwnProfile ? true : hasUserUpdatePermission;

  return {
    handleSubmit,
    isOwnProfile,
    canUpdateUser,
    initialValues,
  };
};

interface ReinviteSectionProps {
  user: User;
}

const ReinviteSection = ({ user }: ReinviteSectionProps) => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [reinviteUser, { isLoading }] = useReinviteUserMutation();
  const { handleError } = useAPIHelper();
  const { successAlert } = useAlert();
  const canReinvite = useHasPermission([ScopeRegistryEnum.USER_CREATE]);

  if (!user.has_invite || !canReinvite) {
    return null;
  }

  const handleReinvite = async () => {
    try {
      await reinviteUser(user.id).unwrap();
      successAlert(
        "User reinvited successfully. A new invitation email has been sent.",
      );
      setIsModalOpen(false);
    } catch (error) {
      handleError(error);
    }
  };

  return (
    <>
      <Box mb={4}>
        <Alert
          message={user.invite_expired ? "Invite expired" : "Invite pending"}
          description={
            user.invite_expired
              ? "This user's invitation has expired. Use the button to send a new invitation email."
              : "This user has not yet accepted their invitation. You can resend the invitation if needed."
          }
          type={user.invite_expired ? "warning" : "info"}
          showIcon
          action={
            <Button
              type="primary"
              onClick={() => setIsModalOpen(true)}
              loading={isLoading}
            >
              Reinvite user
            </Button>
          }
        />
      </Box>

      <Modal
        title="Reinvite user"
        open={isModalOpen}
        onOk={handleReinvite}
        onCancel={() => setIsModalOpen(false)}
        okText="Reinvite"
        cancelText="Cancel"
        confirmLoading={isLoading}
      >
        <Text>
          Are you sure you want to send a new invitation to {user.username}? A
          new invitation email will be sent to {user.email_address}.
        </Text>
        {!user.invite_expired ? (
          <Text>The previous invitation code will no longer be valid.</Text>
        ) : null}
      </Modal>
    </>
  );
};

interface Props {
  user: User;
}
const EditUserForm = ({ user }: Props) => {
  const { handleSubmit, canUpdateUser, initialValues } = useUserForm(user);

  const canViewAllUsers = useHasPermission([ScopeRegistryEnum.USER_READ]);

  return (
    <div>
      <PageHeader
        heading="Users"
        breadcrumbItems={[
          {
            title: "All users",
            href: canViewAllUsers ? USER_MANAGEMENT_ROUTE : undefined,
          },
          { title: initialValues.username },
        ]}
      />
      <ReinviteSection user={user} />
      <UserManagementTabs
        onSubmit={handleSubmit}
        initialValues={initialValues}
        canEditNames={canUpdateUser}
      />
    </div>
  );
};

export default EditUserForm;
