import { Alert, Button, Modal, useMessage } from "fidesui";
import React from "react";
import { useSelector } from "react-redux";
import UserManagementTabs from "user-management/UserManagementTabs";

import { selectUser } from "~/features/auth";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import { useHasPermission } from "~/features/common/Restrict";
import { ScopeRegistryEnum, UserCreateExtended } from "~/types/api";

import { useAPIHelper } from "../common/hooks";
import PageHeader from "../common/PageHeader";
import { User } from "./types";
import {
  useEditUserMutation,
  useReinviteUserMutation,
} from "./user-management.slice";
import { type FormValues } from "./UserForm";

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

  const handleSubmit = async (values: UserCreateExtended) => {
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
  const [reinviteUser, { isLoading }] = useReinviteUserMutation();
  const { handleError } = useAPIHelper();
  const message = useMessage();
  const [modal, contextHolder] = Modal.useModal();
  const canReinvite = useHasPermission([ScopeRegistryEnum.USER_CREATE]);

  if (!user.has_invite || !canReinvite) {
    return null;
  }

  const handleReinviteClick = () => {
    const content = (
      <>
        <p>
          Are you sure you want to send a new invitation to {user.username}? A
          new invitation email will be sent to {user.email_address}.
        </p>
        {!user.invite_expired ? (
          <p>The previous invitation code will no longer be valid.</p>
        ) : null}
      </>
    );

    modal.confirm({
      title: "Reinvite user",
      content,
      okText: "Reinvite",
      cancelText: "Cancel",
      onOk: async () => {
        try {
          await reinviteUser(user.id).unwrap();
          message.success(
            "User reinvited successfully. A new invitation email has been sent.",
          );
        } catch (error) {
          handleError(error);
        }
      },
    });
  };

  return (
    <>
      {contextHolder}
      <div className="mb-4">
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
              onClick={handleReinviteClick}
              loading={isLoading}
            >
              Reinvite user
            </Button>
          }
        />
      </div>
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
