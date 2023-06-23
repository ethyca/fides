import { Heading, Spinner, Stack, Text } from "@fidesui/react";
import NextLink from "next/link";

import { SystemResponse } from "~/types/api";

import { usePrivacyDeclarationData } from "./hooks";
import PrivacyDeclarationManager from "./PrivacyDeclarationManager";

interface Props {
  system: SystemResponse;
}

const PrivacyDeclarationStep = ({ system }: Props) => {
  const { isLoading, ...dataProps } = usePrivacyDeclarationData({
    includeDatasets: true,
  });

  return (
    <Stack spacing={3} data-testid="privacy-declaration-step">
      <Heading as="h3" size="md">
        Data uses
      </Heading>
      <Text fontSize="sm">
        Data Uses describe the business purpose for which the personal data is
        processed or collected. Within a Data Use, you assign which categories
        of personal information are collected for this purpose and for which
        categories of data subjects. To update the available categories and
        uses, please visit{" "}
        <NextLink href="/taxonomy" passHref>
          <Text as="a" color="complimentary.600">
            Manage taxonomy
          </Text>
        </NextLink>
        .
      </Text>
      {isLoading ? (
        <Spinner />
      ) : (
        <PrivacyDeclarationManager
          system={system}
          includeCustomFields
          includeCookies
          {...dataProps}
        />
      )}
    </Stack>
  );
};

export default PrivacyDeclarationStep;
