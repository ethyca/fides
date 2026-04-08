import { Button, Flex, Table } from "fidesui";
import { useRouter } from "next/router";

import { PRIVACY_EXPERIENCE_ROUTE } from "~/features/common/nav/routes";
import Restrict from "~/features/common/Restrict";
import CustomAssetUploadButton from "~/features/custom-assets/CustomAssetUploadButton";
import JavaScriptTag from "~/features/privacy-experience/JavaScriptTag";
import usePrivacyExperiencesTable from "~/features/privacy-experience/usePrivacyExperiencesTable";
import { CustomAssetType, ScopeRegistryEnum } from "~/types/api";

export const PrivacyExperiencesTable = () => {
  const { tableProps, columns, userCanUpdate } = usePrivacyExperiencesTable();
  const router = useRouter();

  return (
    <Flex vertical gap="middle" style={{ width: "100%" }}>
      {userCanUpdate && (
        <Flex justify="space-between" align="center">
          <Flex gap="small">
            <JavaScriptTag />
            <Restrict scopes={[ScopeRegistryEnum.CUSTOM_ASSET_UPDATE]}>
              <CustomAssetUploadButton
                assetType={CustomAssetType.CUSTOM_FIDES_CSS}
              />
            </Restrict>
          </Flex>
          <Button
            onClick={() => router.push(`${PRIVACY_EXPERIENCE_ROUTE}/new`)}
            type="primary"
            data-testid="add-privacy-experience-btn"
          >
            Create new experience
          </Button>
        </Flex>
      )}
      <Table {...tableProps} columns={columns} />
    </Flex>
  );
};
