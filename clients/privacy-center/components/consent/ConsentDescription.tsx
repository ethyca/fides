import { ChakraBox as Box, ChakraTextProps as TextProps } from "fidesui";

import { useAppSelector } from "~/app/hooks";
import useI18n from "~/common/hooks/useI18n";
import TextOrHtml from "~/components/TextOrHtml";
import { useConfig } from "~/features/common/config.slice";
import {
  selectIsNoticeDriven,
  useSettings,
} from "~/features/common/settings.slice";

const TEXT_PROPS: TextProps = {
  fontSize: ["small", "medium"],
  fontWeight: "normal",
  maxWidth: 624,
  textAlign: "center",
  color: "gray.800",
};

const ConsentDescription = () => {
  const config = useConfig();
  const isNoticeDriven = useAppSelector(selectIsNoticeDriven);
  const { ALLOW_HTML_DESCRIPTION } = useSettings();
  const { i18n } = useI18n();

  if (!isNoticeDriven) {
    return (
      <Box className="pc-page__description" data-testid="consent-description">
        <TextOrHtml
          {...TEXT_PROPS}
          data-testid="description"
          allowHTMLDescription={ALLOW_HTML_DESCRIPTION}
        >
          {config.consent?.page.description ?? ""}
        </TextOrHtml>
        {config.consent?.page.description_subtext?.map((paragraph, index) => (
          <TextOrHtml
            {...TEXT_PROPS}
            allowHTMLDescription={ALLOW_HTML_DESCRIPTION}
            // eslint-disable-next-line react/no-array-index-key
            key={`description-subtext${index}`}
          >
            {paragraph}
          </TextOrHtml>
        ))}
      </Box>
    );
  }
  return (
    <TextOrHtml
      className="pc-page__description"
      {...TEXT_PROPS}
      data-testid="consent-description"
      allowHTMLDescription={ALLOW_HTML_DESCRIPTION}
    >
      {i18n.t("exp.description")}
    </TextOrHtml>
  );
};

export default ConsentDescription;
