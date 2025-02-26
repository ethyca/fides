import { RoleRegistryEnum } from "~/types/api";

export const ROLES = [
  {
    label: "Owner",
    permissions_label: "Owner",
    roleKey: RoleRegistryEnum.OWNER,
    description:
      "Owners have view and edit access to the whole organization and can create new users",
  },
  {
    label: "Contributor",
    permissions_label: "Contributor",
    roleKey: RoleRegistryEnum.CONTRIBUTOR,
    description:
      "Contributors can create new users and have view and edit access to the whole organization. Contributors cannot configure storage and messaging services",
  },
  {
    label: "Viewer",
    permissions_label: "Viewer",
    roleKey: RoleRegistryEnum.VIEWER,
    description: "Viewers have view access to the Data Map and all systems",
  },
  {
    label: "Viewer & Approver",
    permissions_label: "Viewer & Approver",
    roleKey: RoleRegistryEnum.VIEWER_AND_APPROVER,
    description:
      "Viewer & Approvers have view access to the Data Map but can also manage Privacy Requests",
  },
  {
    label: "Approver",
    permissions_label: "Approver",
    roleKey: RoleRegistryEnum.APPROVER,
    description:
      "Approvers can only access the Privacy Requests portal to manage requests",
  },
];
