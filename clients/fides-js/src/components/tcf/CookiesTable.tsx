import { h } from "preact";

const CookiesTable = () => (
  <table className="fides-cookies-table">
    <thead>
      <tr>
        <th>Category</th>
        <th>Cookie</th>
        <th>Domain</th>
        <th>Duration</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>Store and/or access information on a device</td>
        <td>_cookie_</td>
        <td>domain</td>
        <td>45 days</td>
      </tr>
    </tbody>
  </table>
);

export default CookiesTable;
