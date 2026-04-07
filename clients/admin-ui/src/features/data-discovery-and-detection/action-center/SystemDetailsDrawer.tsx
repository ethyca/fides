import { skipToken } from "@reduxjs/toolkit/query";
import { Descriptions, Flex, Paragraph, SparkleIcon, Tooltip } from "fidesui";
import { upperFirst } from "lodash";
import { useQueryState } from "nuqs";

import { useGetStagedResourceDetailsQuery } from "./action-center.slice";
import { DetailsDrawer } from "./fields/DetailsDrawer";
import { SystemDataUsesForm } from "./forms/SystemDataUsesForm";
import { SystemDescriptionForm } from "./forms/SystemDescriptionForm";
import { useInfrastructureActions } from "./hooks/useInfrastructureActions";

interface SystemDetailsDrawerProps {
  monitorId: string;
}

export const SystemDetailsDrawer = ({
  monitorId,
}: SystemDetailsDrawerProps) => {
  const [stagedResourceUrn, setStagedResourceUrn] =
    useQueryState("stagedResourceUrn");
  const { data: resourceDetails, isLoading } = useGetStagedResourceDetailsQuery(
    stagedResourceUrn ? { stagedResourceUrn } : skipToken,
  );
  const actions = useInfrastructureActions({
    urn: stagedResourceUrn ?? undefined,
    monitorId,
    diffStatus: resourceDetails?.diff_status ?? undefined,
  });

  return (
    <DetailsDrawer
      title={resourceDetails?.name ?? stagedResourceUrn}
      itemKey={stagedResourceUrn ?? ""}
      actions={Object.entries(actions).flatMap(([name, action]) =>
        action.hidden
          ? []
          : [
              {
                label: upperFirst(name),
                ...action,
              },
            ],
      )}
      destroyOnHidden
      open={!!stagedResourceUrn}
      loading={isLoading}
      onClose={() => setStagedResourceUrn(null)}
    >
      <Flex vertical gap="medium">
        <Descriptions
          size="small"
          layout="vertical"
          colon={false}
          classNames={{ label: "!text-black !font-semibold" }}
          items={[
            {
              key: "id",
              label: "Id",
              children: (
                <Paragraph ellipsis={{ rows: 1 }}>
                  {resourceDetails?.urn}
                </Paragraph>
              ),
              span: "filled",
            },
            {
              key: "description",
              span: "filled",
              label: (
                <Tooltip>
                  <Flex gap="small" align="center">
                    <span>Description</span>
                    {!resourceDetails?.user_assigned_description ? (
                      <SparkleIcon />
                    ) : null}
                  </Flex>
                </Tooltip>
              ),
              children:
                resourceDetails &&
                resourceDetails?.urn === stagedResourceUrn ? (
                  <SystemDescriptionForm
                    monitorId={monitorId}
                    stagedResourceUrn={stagedResourceUrn}
                    initialValues={{
                      description:
                        resourceDetails.user_assigned_description ??
                        resourceDetails.description ??
                        "",
                    }}
                  />
                ) : null,
            },
            {
              key: "dataUses",
              label: "Data uses",
              span: "filled",
              children:
                !!resourceDetails &&
                resourceDetails?.urn === stagedResourceUrn &&
                !isLoading ? (
                  <SystemDataUsesForm
                    monitorId={monitorId}
                    stagedResourceUrn={stagedResourceUrn}
                    initialValues={{
                      dataUses:
                        "user_assigned_data_uses" in resourceDetails &&
                        Array.isArray(resourceDetails.user_assigned_data_uses)
                          ? resourceDetails.user_assigned_data_uses
                          : (resourceDetails.data_uses ?? []),
                    }}
                  />
                ) : null,
            },
          ]}
        />
      </Flex>
    </DetailsDrawer>
  );
};
