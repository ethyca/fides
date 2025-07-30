import { useI18n } from "../../lib/i18n/i18n-context";
import InfoBox from "../InfoBox";

export const TcfLoadingErrorMessage = ({
  generalLabel,
  specificLabel,
}: {
  generalLabel: string;
  specificLabel: string;
}) => {
  // TODO: [ENG-1050] add translations for the error messages
  const { i18n } = useI18n();
  return (
    <InfoBox
      style={{
        backgroundColor: "var(--fides-overlay-background-error-color)",
      }}
      data-testid="tcf-loading-error-message"
    >
      There was an error loading the {generalLabel}. You may{" "}
      <strong>{i18n.t("exp.accept_button_label").toLocaleLowerCase()}</strong>{" "}
      or{" "}
      <strong>{i18n.t("exp.reject_button_label").toLocaleLowerCase()}</strong>,
      but in order to exercise your rights for {specificLabel}, please try again
      later. If the problem persists, please contact the site owner.
    </InfoBox>
  );
};
