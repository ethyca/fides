import type { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { PROPERTIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { FormBuilderPage } from "~/features/properties/privacy-center-config/form-builder/FormBuilderPage";
import type {
  JsonRenderSpec,
  MapResult,
  PcCustomFields,
} from "~/features/properties/privacy-center-config/form-builder/mapper";
import {
  useGetPropertyByIdQuery,
  useUpdatePropertyMutation,
} from "~/features/properties/property.slice";

const FormBuilderRoute: NextPage = () => {
  const router = useRouter();
  const { id, actionPolicyKey } = router.query as {
    id?: string;
    actionPolicyKey?: string;
  };
  const { data: property, isLoading } = useGetPropertyByIdQuery(id ?? "", {
    skip: !id,
  });
  const [updateProperty] = useUpdatePropertyMutation();
  const matchedAction = (
    (property?.privacy_center_config as { actions?: any[] } | null)?.actions ??
    []
  ).find((a) => a?.policy_key === actionPolicyKey);
  const breadcrumbTitle = matchedAction?.title || actionPolicyKey;

  const handleSave = async ({
    actionPolicyKey: key,
    pcShape,
    identityInputs,
    richSpec,
  }: {
    actionPolicyKey: string;
    pcShape: PcCustomFields;
    identityInputs: MapResult["identityInputs"];
    richSpec: JsonRenderSpec;
  }) => {
    if (!property) {
      return;
    }
    const config = property.privacy_center_config ?? { actions: [] };
    const existingActions = (config as { actions?: any[] }).actions ?? [];
    const actions = existingActions.map((action: any) =>
      action.policy_key === key
        ? {
            ...action,
            custom_privacy_request_fields: pcShape,
            identity_inputs:
              Object.keys(identityInputs).length > 0 ? identityInputs : null,
            // eslint-disable-next-line no-underscore-dangle
            _form_builder_spec: {
              version: 1,
              spec: richSpec,
              updated_at: new Date().toISOString(),
            },
          }
        : action,
    );
    // eslint-disable-next-line @typescript-eslint/naming-convention
    const { id: propertyId, messaging_templates, ...rest } = property as any;
    await updateProperty({
      id: propertyId,
      property: {
        ...rest,
        privacy_center_config: { ...config, actions },
      },
    }).unwrap();
  };

  if (isLoading || !property || !actionPolicyKey) {
    return null;
  }

  return (
    <Layout title="Form editor">
      <PageHeader
        heading="Form editor"
        breadcrumbItems={[
          { title: "All properties", href: PROPERTIES_ROUTE },
          { title: property.name, href: `${PROPERTIES_ROUTE}/${property.id}` },
          { title: breadcrumbTitle },
        ]}
      />
      <FormBuilderPage
        propertyId={property.id!}
        property={property as any}
        actionPolicyKey={actionPolicyKey}
        onSave={handleSave}
      />
    </Layout>
  );
};

export default FormBuilderRoute;
