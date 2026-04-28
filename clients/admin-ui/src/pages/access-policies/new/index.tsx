import { useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { useCreateAccessPolicyMutation } from "~/features/access-policies/access-policies.slice";
import AccessPolicyEditor, {
  SidebarFormValues,
} from "~/features/access-policies/AccessPolicyEditor";
import { getErrorMessage } from "~/features/common/helpers";
import { ACCESS_POLICIES_ROUTE } from "~/features/common/nav/routes";
import { RTKErrorResult } from "~/types/errors";

const NewAccessPolicyPage: NextPage = () => {
  const router = useRouter();
  const messageApi = useMessage();
  const [createAccessPolicy] = useCreateAccessPolicyMutation();

  const handleSave = async (values: SidebarFormValues, yaml: string) => {
    try {
      await createAccessPolicy({
        ...values,
        yaml,
      }).unwrap();
      messageApi.success("Policy created.");
      router.push(ACCESS_POLICIES_ROUTE);
    } catch (error) {
      messageApi.error(getErrorMessage(error as RTKErrorResult["error"]));
    }
  };

  return <AccessPolicyEditor onSave={handleSave} />;
};

export default NewAccessPolicyPage;
