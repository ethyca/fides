import "./CustomSpinner.css";

interface CustomSpinnerProps {
  size?: string;
}

export const CustomSpinner = ({ size = "14px" }: CustomSpinnerProps) => (
  <div className="custom-spinner" style={{ width: size, height: size }}>
    <div className="custom-spinner-dot custom-spinner-dot-1" />
    <div className="custom-spinner-dot custom-spinner-dot-2" />
    <div className="custom-spinner-dot custom-spinner-dot-3" />
    <div className="custom-spinner-dot custom-spinner-dot-4" />
  </div>
);
