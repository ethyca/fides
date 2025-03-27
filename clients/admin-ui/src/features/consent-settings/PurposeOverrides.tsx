import { Box, Flex, Text } from "fidesui";
import { FieldArray, useFormikContext } from "formik";

import { useAppSelector } from "~/app/hooks";
import { CustomSwitch } from "~/features/common/form/inputs";
import { selectPurposes } from "~/features/common/purpose.slice";

type FormPurposeOverride = {
  purpose: number;
  is_included: boolean;
  is_consent: boolean;
  is_legitimate_interest: boolean;
};

const LegalBasisContainer = ({
  children,
  purpose,
  endCol,
}: {
  children: React.ReactNode;
  purpose: number;
  endCol?: boolean;
}) => {
  const hiddenPurposes = [1, 3, 4, 5, 6];

  return (
    <Flex
      flex="1"
      justifyContent="center"
      alignItems="center"
      borderLeft="solid 1px"
      borderRight={endCol ? "solid 1px" : "unset"}
      borderColor="gray.200"
      height="100%"
      minWidth="36px"
    >
      {hiddenPurposes.includes(purpose) ? null : <Box>{children}</Box>}
    </Flex>
  );
};

const PurposeOverrides = () => {
  const { values, setFieldValue } = useFormikContext<{
    purposeOverrides: FormPurposeOverride[];
  }>();
  const { purposes: purposeMapping } = useAppSelector(selectPurposes);
  return (
    <FieldArray
      name="purposeOverrides"
      render={() => (
        <Flex flexDirection="column" minWidth="944px">
          <Flex
            width="100%"
            border="solid 1px"
            borderColor="gray.200"
            backgroundColor="gray.50"
            height="36px"
          >
            <Flex
              width="600px"
              pl="4"
              fontSize="xs"
              fontWeight="medium"
              lineHeight="4"
              alignItems="center"
              borderRight="solid 1px"
              borderColor="gray.200"
            >
              TCF purpose
            </Flex>
            <Flex
              flex="1"
              alignItems="center"
              borderRight="solid 1px"
              borderColor="gray.200"
              minWidth="36px"
            >
              <Text pl="4" fontSize="xs" fontWeight="medium" lineHeight="4">
                Allowed
              </Text>
            </Flex>
            <Flex
              flex="1"
              alignItems="center"
              borderRight="solid 1px"
              borderColor="gray.200"
            >
              <Text pl="4" fontSize="xs" fontWeight="medium" lineHeight="4">
                Consent
              </Text>
            </Flex>
            <Flex flex="1" alignItems="center">
              <Text pl="4" fontSize="xs" fontWeight="medium" lineHeight="4">
                Legitimate interest
              </Text>
            </Flex>
          </Flex>
          {values.purposeOverrides.map((po, index) => (
            <Flex
              key={po.purpose}
              width="100%"
              height="36px"
              alignItems="center"
              borderBottom="solid 1px"
              borderColor="gray.200"
            >
              <Flex
                width="600px"
                borderLeft="solid 1px"
                borderColor="gray.200"
                p={0}
                alignItems="center"
                height="100%"
                pl="4"
                fontSize="xs"
                fontWeight="normal"
                lineHeight="4"
              >
                Purpose {po.purpose}: {purposeMapping[po.purpose].name}
              </Flex>

              <Flex
                flex="1"
                justifyContent="center"
                alignItems="center"
                borderLeft="solid 1px"
                borderColor="gray.200"
                height="100%"
              >
                <Box>
                  <CustomSwitch
                    name={`purposeOverrides[${index}].is_included`}
                    onChange={(checked) => {
                      if (!checked) {
                        setFieldValue(
                          `purposeOverrides[${index}].is_consent`,
                          false,
                        );
                        setFieldValue(
                          `purposeOverrides[${index}].is_legitimate_interest`,
                          false,
                        );
                      }
                    }}
                  />
                </Box>
              </Flex>
              <LegalBasisContainer purpose={po.purpose}>
                <CustomSwitch
                  isDisabled={
                    !values.purposeOverrides[index].is_included ||
                    values.purposeOverrides[index].is_legitimate_interest
                  }
                  name={`purposeOverrides[${index}].is_consent`}
                />
              </LegalBasisContainer>
              <LegalBasisContainer purpose={po.purpose} endCol>
                <CustomSwitch
                  isDisabled={
                    !values.purposeOverrides[index].is_included ||
                    values.purposeOverrides[index].is_consent
                  }
                  name={`purposeOverrides[${index}].is_legitimate_interest`}
                />
              </LegalBasisContainer>
            </Flex>
          ))}
        </Flex>
      )}
    />
  );
};
export default PurposeOverrides;
