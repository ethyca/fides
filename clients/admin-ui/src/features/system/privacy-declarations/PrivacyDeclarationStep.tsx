import { Heading, Spinner, Stack, Text } from "@fidesui/react";
import NextLink from "next/link";

import { usePrivacyDeclarationData } from "~/features/system/privacy-declarations/hooks";
import PrivacyDeclarationFormTab from "~/features/system/system-form-declaration-tab/PrivacyDeclarationFormTab";
import { SystemResponse } from "~/types/api";

interface Props {
  system: SystemResponse;
}

const PrivacyDeclarationStep = ({ system }: Props) => {
  const { isLoading, ...dataProps } = usePrivacyDeclarationData({
    includeDatasets: true,
    includeDisabled: false,
  });

  const allEnabledDataCategories = dataProps.allDataCategories.filter(
    (category) => category.active
  );

  const allEnabledDataUses = dataProps.allDataUses.filter((use) => use.active);

  const allEnabledDataSubjects = dataProps.allDataSubjects.filter(
    (subject) => subject.active
  );

  const filteredDataProps = {
    ...dataProps,
    allDataCategories: allEnabledDataCategories,
    allDataUses: allEnabledDataUses,
    allDataSubject: allEnabledDataSubjects,
    cookies: system.cookies,
  };

  return (
    <Stack spacing={3} data-testid="privacy-declaration-step" minWidth={580}>
      <Heading as="h3" size="md">
        Data uses
      </Heading>
      <Text fontSize="sm" fontWeight="medium">
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
        <PrivacyDeclarationFormTab
          system={system}
          includeCustomFields
          includeCookies
          {...filteredDataProps}
        />
      )}
    </Stack>
  );
};

export default PrivacyDeclarationStep;
