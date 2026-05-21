import { Result } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { PROPERTIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { FormBuilderPage } from "~/features/properties/privacy-center-config/form-builder/FormBuilderPage";
import type {
  MapResult,
  PcCustomFields,
} from "~/features/properties/privacy-center-config/form-builder/types";
import {
  useGetPropertyByIdQuery,
  useUpdatePropertyMutation,
} from "~/features/properties/property.slice";

const FormBuilderRoute: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();
  const { id, actionPolicyKey } = router.query as {
    id?: string;
    actionPolicyKey?: string;
  };
  const { data: property, isLoading } = useGetPropertyByIdQuery(id ?? "", {
    skip: !id,
  });
  const [updateProperty] = useUpdatePropertyMutation();
  const matchedAction = (property?.privacy_center_config?.actions ?? []).find(
    (a) => a?.policy_key === actionPolicyKey,
  );
  const breadcrumbTitle = matchedAction?.title || actionPolicyKey;

  const handleSave = async ({
    actionPolicyKey: key,
    pcShape,
    identityInputs,
    fieldOrder,
  }: {
    actionPolicyKey: string;
    pcShape: PcCustomFields;
    identityInputs: MapResult["identityInputs"];
    fieldOrder: MapResult["fieldOrder"];
  }) => {
    if (!property?.privacy_center_config) {
      return;
    }
    const config = property.privacy_center_config;
    const existingActions = config.actions ?? [];
    let found = false;
    const actions = existingActions.map((action) => {
      if (action.policy_key !== key) {
        return action;
      }
      found = true;
      return {
        ...action,
        custom_privacy_request_fields: pcShape,
        identity_inputs:
          Object.keys(identityInputs).length > 0 ? identityInputs : null,
        field_order: fieldOrder,
      };
    });
    if (!found) {
      throw new Error(
        "Action not found — it may have been deleted or renamed.",
      );
    }
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const { id: propertyId, messaging_templates, ...rest } = property;
    await updateProperty({
      id: propertyId!,
      property: {
        ...rest,
        privacy_center_config: {
          ...config,
          actions,
        } as typeof config,
      },
    }).unwrap();
  };

  if (!flags.formBuilder) {
    return (
      <Layout title="Form builder">
        <Result
          status="error"
          title="Form builder is not enabled"
          subTitle="Turn on the form builder flag to preview this feature."
        />
      </Layout>
    );
  }

  if (isLoading || !property || !actionPolicyKey) {
    return null;
  }

  return (
    <Layout title="Form builder">
      <PageHeader
        heading="Form builder"
        breadcrumbItems={[
          { title: "All properties", href: PROPERTIES_ROUTE },
          { title: property.name, href: `${PROPERTIES_ROUTE}/${property.id}` },
          { title: breadcrumbTitle },
        ]}
      />
      <FormBuilderPage
        propertyId={property.id!}
        property={property}
        actionPolicyKey={actionPolicyKey}
        onSave={handleSave}
      />
    </Layout>
  );
};

export default FormBuilderRoute;
