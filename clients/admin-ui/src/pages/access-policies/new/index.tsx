import { useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import AccessPolicyEditor from "~/features/access-policies/AccessPolicyEditor";
import { ACCESS_POLICIES_ROUTE } from "~/features/common/nav/routes";

const NewAccessPolicyPage: NextPage = () => {
  const router = useRouter();
  const messageApi = useMessage();

  const handleSave = async () => {
    messageApi.success("Policy created.");
    router.push(ACCESS_POLICIES_ROUTE);
  };

  return <AccessPolicyEditor onSave={handleSave} />;
};

export default NewAccessPolicyPage;
