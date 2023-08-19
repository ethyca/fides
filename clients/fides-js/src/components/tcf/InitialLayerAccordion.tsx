import { h } from "preact";
import { useDisclosure } from "../../lib/hooks";

const ArrowDown = () => (
  <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none">
    <path
      fill="#2D3748"
      d="m12 13.172 4.95-4.95 1.414 1.414L12 16 5.636 9.636 7.05 8.222l4.95 4.95Z"
    />
  </svg>
);

const InitialLayerAccordion = ({
  title,
  description,
}: {
  title: string;
  description: string;
}) => {
  const { isOpen, getButtonProps, getDisclosureProps, onToggle } =
    useDisclosure({
      id: title,
    });

  const handleKeyDown = (event: KeyboardEvent) => {
    if (event.code === "Space" || event.code === "Enter") {
      onToggle();
    }
  };

  return (
    <div
      className={
        isOpen
          ? "fides-notice-toggle fides-notice-toggle-expanded"
          : "fides-notice-toggle"
      }
    >
      <span
        role="button"
        tabIndex={0}
        onKeyDown={handleKeyDown}
        {...getButtonProps()}
        className="fides-notice-toggle-trigger"
      >
        {title}
        <ArrowDown />
      </span>
      <div {...getDisclosureProps()}>{description}</div>
    </div>
  );
};

export default InitialLayerAccordion;
