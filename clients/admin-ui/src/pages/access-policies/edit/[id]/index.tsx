import { useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import {
  useDeleteAccessPolicyMutation,
  useGetAccessPolicyQuery,
  useUpdateAccessPolicyMutation,
} from "~/features/access-policies/access-policies.slice";
import AccessPolicyEditor, {
  SidebarFormValues,
} from "~/features/access-policies/AccessPolicyEditor";
import { getErrorMessage } from "~/features/common/helpers";
import { ACCESS_POLICIES_ROUTE } from "~/features/common/nav/routes";
import { RTKErrorResult } from "~/types/errors";

const EditAccessPolicyPage: NextPage = () => {
  const router = useRouter();
  const messageApi = useMessage();
  const { id } = router.query;
  const policyId = id as string;

  const { data } = useGetAccessPolicyQuery(policyId, { skip: !policyId });
  const [updateAccessPolicy] = useUpdateAccessPolicyMutation();
  const [deleteAccessPolicy] = useDeleteAccessPolicyMutation();

  const handleSave = async (values: SidebarFormValues, yaml: string) => {
    try {
      await updateAccessPolicy({ id: policyId, ...values, yaml }).unwrap();
      messageApi.success("Policy saved.");
    } catch (error) {
      messageApi.error(getErrorMessage((error as RTKErrorResult).error));
    }
  };

  const handleDelete = async () => {
    try {
      await deleteAccessPolicy(policyId).unwrap();
      router.push(ACCESS_POLICIES_ROUTE);
    } catch (error) {
      messageApi.error(getErrorMessage((error as RTKErrorResult).error));
    }
  };

  return (
    <AccessPolicyEditor
      policyId={policyId}
      initialValues={data}
      onSave={handleSave}
      onDelete={handleDelete}
    />
  );
};

export default EditAccessPolicyPage;
