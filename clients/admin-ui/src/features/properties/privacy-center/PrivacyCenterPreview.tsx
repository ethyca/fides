import {
  ChakraBox as Box,
  ChakraDivider as Divider,
  ChakraFlex as Flex,
  ChakraHeading as Heading,
  ChakraImage as Image,
  ChakraText as Text,
} from "fidesui";
import { useFormikContext } from "formik";

import type { PropertyFormValues } from "../PropertyForm";

const sanitizeIconSrc = (iconPath?: string | null): string | undefined => {
  if (!iconPath) {
    return undefined;
  }

  try {
    const url = new URL(iconPath, typeof window !== "undefined" ? window.location.origin : "http://localhost");
    if (url.protocol === "http:" || url.protocol === "https:") {
      return url.toString();
    }
    return undefined;
  } catch {
    if (iconPath.startsWith("/")) {
      return iconPath;
    }
    return undefined;
  }
};

const ActionCard = ({
  title,
  description,
  iconPath,
}: {
  title: string;
  description: string;
  iconPath?: string | null;
}) => {
  const safeIconSrc = sanitizeIconSrc(iconPath);

  return (
    <Flex
      border="1px solid"
      borderColor="gray.200"
      borderRadius="lg"
      p={5}
      gap={3}
      flex="1"
      minWidth="120px"
      flexDirection="column"
      alignItems="flex-start"
      textAlign="left"
      backgroundColor="white"
      _hover={{ borderColor: "gray.400", boxShadow: "sm" }}
      cursor="default"
      data-testid="preview-action-card"
    >
      {safeIconSrc && (
        <Box flexShrink={0} mt={0.5}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={safeIconSrc}
            alt=""
            style={{ width: 24, height: 24, objectFit: "contain" }}
          />
        </Box>
      )}
      <Box>
        <Text fontWeight="semibold" fontSize="sm" color="gray.800">
          {title || <span style={{ color: "#aaa" }}>Action title</span>}
        </Text>
        <Text fontSize="xs" color="gray.600" mt={1}>
          {description || (
            <span style={{ color: "#aaa" }}>Action description</span>
          )}
        </Text>
      </Box>
    </Flex>
  );
};

const PrivacyCenterPreview = () => {
  const { values } = useFormikContext<PropertyFormValues>();
  const config = values.privacy_center_config;

  return (
    <Box
      backgroundColor="gray.50"
      minHeight="100%"
      p={8}
      borderRadius="md"
      border="1px solid"
      borderColor="gray.200"
      data-testid="privacy-center-preview"
    >
      <Box maxWidth="600px" mx="auto">
        {/* Logo */}
        {(config?.logo_url || config?.logo_path) && (
          <Box mb={6} textAlign="center">
            <Image
              src={config.logo_url || config.logo_path || ""}
              alt="Logo"
              maxHeight="60px"
              objectFit="contain"
              display="inline-block"
            />
          </Box>
        )}

        {/* Title */}
        <Heading
          as="h1"
          fontSize="xl"
          fontWeight="bold"
          color="gray.800"
          textAlign="center"
          mb={3}
        >
          {config?.title || (
            <Text as="span" color="gray.400" fontStyle="italic">
              Privacy center title
            </Text>
          )}
        </Heading>

        {/* Description */}
        <Text
          fontSize="sm"
          color="gray.600"
          textAlign="center"
          mb={config?.description_subtext?.length ? 2 : 6}
        >
          {config?.description || (
            <span style={{ color: "#aaa", fontStyle: "italic" }}>
              Description
            </span>
          )}
        </Text>

        {/* Description subtext */}
        {(config?.description_subtext ?? []).filter(Boolean).map(
          (line, i) =>
            line && (
              <Text
                // eslint-disable-next-line react/no-array-index-key
                key={i}
                fontSize="xs"
                color="gray.500"
                textAlign="center"
                mb={1}
              >
                {line}
              </Text>
            ),
        )}

        <Divider my={5} />

        {/* Action cards */}
        <Flex gap={3} flexWrap="wrap">
          {(config?.actions ?? []).length === 0 && (
            <Text
              fontSize="sm"
              color="gray.400"
              fontStyle="italic"
              textAlign="center"
            >
              No actions configured
            </Text>
          )}
          {(config?.actions ?? []).map((action, i) => (
            <ActionCard
              // eslint-disable-next-line react/no-array-index-key
              key={i}
              title={action.title}
              description={action.description}
              iconPath={action.icon_path}
            />
          ))}
        </Flex>

        {/* Links */}
        {(config?.links ?? []).length > 0 && (
          <Flex justifyContent="center" gap={4} mt={6} flexWrap="wrap">
            {(config.links ?? []).map((link, i) => (
              // eslint-disable-next-line react/no-array-index-key
              <Text key={i} fontSize="xs" color="gray.500">
                {link.label}
              </Text>
            ))}
          </Flex>
        )}
      </Box>
    </Box>
  );
};

export default PrivacyCenterPreview;
