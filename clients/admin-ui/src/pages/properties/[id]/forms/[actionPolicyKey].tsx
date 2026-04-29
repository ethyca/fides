import type { NextPage } from "next";
import { useRouter } from "next/router";

import Layout from "~/features/common/Layout";
import { PROPERTIES_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { FormBuilderPage } from "~/features/properties/privacy-center-config/form-builder/FormBuilderPage";
import type {
  JsonRenderSpec,
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

  const handleSave = async ({
    actionPolicyKey: key,
    pcShape,
    richSpec,
  }: {
    actionPolicyKey: string;
    pcShape: PcCustomFields;
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
    <Layout title="Form Builder">
      <PageHeader
        heading={`Form Builder — ${property.name}`}
        breadcrumbItems={[
          { title: "All properties", href: PROPERTIES_ROUTE },
          { title: property.name, href: `${PROPERTIES_ROUTE}/${property.id}` },
          { title: actionPolicyKey },
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
