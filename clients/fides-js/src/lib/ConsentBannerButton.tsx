import {h, FunctionComponent} from "preact";
import {ButtonType} from "./consent-types";

interface ButtonProps {
    buttonType: ButtonType;
    label?: string,
    onClick?: () => void
}

const ConsentBannerButton: FunctionComponent<ButtonProps> = ({ buttonType, label, onClick }) => (
    <button
        id={`fides-consent-banner-button-${buttonType.valueOf()}`}
        class={`fides-consent-banner-button fides-consent-banner-button-${buttonType.valueOf()}`}
        onClick={onClick}
    >
        {label || ""}
    </button>
);

export default ConsentBannerButton;