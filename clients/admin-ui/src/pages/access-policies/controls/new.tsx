import { useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { useCreateControlMutation } from "~/features/access-policies/access-policies.slice";
import ControlForm, {
  ControlFormValues,
} from "~/features/access-policies/ControlForm";
import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import {
  ACCESS_POLICIES_ROUTE,
  CONTROLS_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { RTKErrorResult } from "~/types/errors/api";

const NewControlPage: NextPage = () => {
  const message = useMessage();
  const router = useRouter();
  const [createControl, { isLoading }] = useCreateControlMutation();

  const handleSubmit = async (values: ControlFormValues) => {
    try {
      await createControl({
        label: values.label,
        description: values.description.trim() || undefined,
      }).unwrap();
      message.success(`Control "${values.label}" created successfully`);
      router.push(CONTROLS_ROUTE);
    } catch (error) {
      message.error(getErrorMessage(error as RTKErrorResult["error"]));
    }
  };

  return (
    <Layout title="New control">
      <PageHeader
        heading="Controls"
        breadcrumbItems={[
          { title: "Access policies", href: ACCESS_POLICIES_ROUTE },
          { title: "Controls", href: CONTROLS_ROUTE },
          { title: "New control" },
        ]}
      />
      <div className="max-w-3xl">
        <ControlForm handleSubmit={handleSubmit} isSubmitting={isLoading} />
      </div>
    </Layout>
  );
};

export default NewControlPage;
