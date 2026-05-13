type PIIProps = {
  data: string | number;
  revealPII: boolean;
};

const PII = ({ data, revealPII }: PIIProps) => {
  const pii = revealPII ? data : String(data).replace(/./g, "*");
  return <>{pii}</>;
};

export default PII;
