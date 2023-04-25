import {h, Component, VNode} from "preact";
import {ButtonType} from "./consent-types";


interface ButtonProps {
    buttonType: ButtonType;
    label?: string,
    onClick: () => void
}

class ConsentBannerButton extends Component<ButtonProps> {

    private readonly buttonType: ButtonType;

    private readonly onClick: () => void;

    private readonly label?: string;

    constructor(props: ButtonProps) {
        super(props);
        this.buttonType = props.buttonType;
        this.onClick = props.onClick;
        this.label = props.label;
    }

    /**
     * Builds a button DOM element with the given id, class name, and text label
     */
    buildButton = (
        buttonType: ButtonType,
        onClick: () => void,
        label?: string
    ) => (
        <button
            id={`fides-consent-banner-button-${buttonType.valueOf()}`}
            class={`fides-consent-banner-button fides-consent-banner-button-${buttonType.valueOf()}`}
            onClick={onClick || undefined}
        >
            {label || ""}
        </button>
    );

    render(): VNode {
        return this.buildButton(this.buttonType, this.onClick, this.label)
    }
}

export default ConsentBannerButton;
