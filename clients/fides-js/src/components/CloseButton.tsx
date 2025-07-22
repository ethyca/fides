const CloseButton = ({
  onClick,
  ariaLabel,
  hidden = false,
}: {
  onClick?: () => void;
  ariaLabel?: string;
  hidden?: boolean;
}) => (
  <button
    type="button"
    aria-label={ariaLabel}
    className="fides-close-button"
    onClick={onClick}
    style={{ visibility: hidden ? "hidden" : "visible" }}
  >
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="none">
      <path
        fill="#2D3748"
        d="m8 7.057 3.3-3.3.943.943-3.3 3.3 3.3 3.3-.943.943-3.3-3.3-3.3 3.3-.943-.943 3.3-3.3-3.3-3.3.943-.943 3.3 3.3Z"
      />
    </svg>
  </button>
);

export default CloseButton;
