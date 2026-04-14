import { Spin, useMessage } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import {
  useGetControlQuery,
  useUpdateControlMutation,
} from "~/features/access-policies/access-policies.slice";
import ControlForm, {
  ControlFormValues,
} from "~/features/access-policies/ControlForm";
import ErrorPage from "~/features/common/errors/ErrorPage";
import { getErrorMessage } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import {
  ACCESS_POLICIES_ROUTE,
  CONTROLS_ROUTE,
} from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { RTKErrorResult } from "~/types/errors/api";

const EditControlPage: NextPage = () => {
  const message = useMessage();
  const router = useRouter();
  const { controlKey } = router.query;

  const {
    data: control,
    error,
    isLoading,
  } = useGetControlQuery(controlKey as string, {
    skip: !controlKey,
  });

  const [updateControl] = useUpdateControlMutation();

  const handleSubmit = async (values: ControlFormValues) => {
    try {
      await updateControl({
        key: controlKey as string,
        label: values.label,
        description: values.description || undefined,
      }).unwrap();
      message.success(`Control "${values.label}" updated successfully`);
      router.push(CONTROLS_ROUTE);
    } catch (err) {
      message.error(getErrorMessage(err as RTKErrorResult["error"]));
    }
  };

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching the control"
      />
    );
  }

  return (
    <Layout title={control?.label ?? "Control"}>
      <PageHeader
        heading="Controls"
        breadcrumbItems={[
          { title: "Access policies", href: ACCESS_POLICIES_ROUTE },
          { title: "Controls", href: CONTROLS_ROUTE },
          { title: control?.label ?? "Control" },
        ]}
      />
      {isLoading ? (
        <Spin />
      ) : (
        <div style={{ maxWidth: 720 }}>
          <ControlForm control={control} handleSubmit={handleSubmit} />
        </div>
      )}
    </Layout>
  );
};

export default EditControlPage;
