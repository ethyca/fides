type PIIProps = {
  data: string | number;
  revealPII: boolean;
};

const PII = ({ data, revealPII }: PIIProps) => {
  const pii = revealPII ? data : String(data).replace(/./g, "*");
  return (
    // eslint-disable-next-line react/jsx-no-useless-fragment
    <>{pii}</>
  );
};

export default PII;
