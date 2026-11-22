import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./style.css";

const reasons = {
  MISSING_IN_B: "Missing in B",
  ORPHAN_IN_B: "Orphan in B",
  DUPLICATE_IN_B: "Duplicate in B",
  VALUE_MISMATCH: "Value mismatch",
  LOCATION_MISMATCH: "Location mismatch",
  DATE_MISMATCH: "Date mismatch",
};

async function getJson(url, signal) {
  const response = await fetch(url, { signal });
  if (!response.ok) throw new Error("The request failed. Refresh to try again.");
  return response.json();
}

function amount(value) {
  // Group the decimal string without converting money into a floating-point number.
  return value == null ? "" : value.replace(/\B(?=(\d{3})+\.)/g, ",");
}

function Findings({ org, reason, sort, toggleSort }) {
  const [rows, setRows] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const request = new AbortController();
    const query = new URLSearchParams({ org, sort });
    if (reason) query.set("reason", reason);
    getJson("/api/disagreements/?" + query, request.signal)
      .then(setRows)
      .catch(err => { if (!request.signal.aborted) setError(err.message); });
    return () => request.abort();
  }, [org, reason, sort]);

  if (error) return <p role="alert">{error}</p>;
  if (!rows) return <p role="status">Loading disagreements…</p>;
  return <section className="panel">
    <div className="summary">{rows.length} {rows.length === 1 ? "disagreement" : "disagreements"} · {org}</div>
    <div className="scroll"><table>
      <thead><tr><th>Reason</th><th>Record ID</th><th>Location</th>
        <th className="numeric" aria-sort={sort === "value" ? "ascending" : "descending"}>
          <button onClick={toggleSort} title="Sort by System A value, using B for orphan entries">
            System A value {sort === "value" ? "↑" : "↓"}
          </button></th>
        <th className="numeric">System B value</th><th className="numeric" title="System B minus System A">Difference</th>
      </tr></thead>
      <tbody>{rows.map(row => <tr key={[row.reason, row.record_id, row.location].join("/")}>
        <td><span className="reason">{reasons[row.reason]}</span></td><td>{row.record_id}</td>
        <td>{row.location}</td><td className="numeric">{amount(row.a_value)}</td>
        <td className="numeric">{amount(row.b_value)}</td>
        <td className="numeric">{amount(row.difference)}</td>
      </tr>)}</tbody>
    </table></div>
    {rows.length === 0 && <p className="empty">No disagreements match this filter.</p>}
  </section>;
}

function App() {
  const [organizations, setOrganizations] = useState([]);
  const [org, setOrg] = useState("");
  const [reason, setReason] = useState("");
  const [sort, setSort] = useState("-value");
  const [error, setError] = useState("");
  useEffect(() => {
    getJson("/api/organizations/").then(items => {
      setOrganizations(items);
      setOrg(items[0] || "");
      if (!items.length) setError("Import the data to see organizations.");
    }).catch(err => setError(err.message));
  }, []);

  return <><header>DealerOS</header><main><h1>Reconciliation</h1>
    <p className="intro">Review differences between System A and System B.</p>
    <div className="controls">
      <label>Organization<select value={org} onChange={event => setOrg(event.target.value)}>
        {organizations.map(item => <option key={item}>{item}</option>)}</select></label>
      <label>Reason<select value={reason} onChange={event => setReason(event.target.value)}>
        <option value="">All reasons</option>
        {Object.entries(reasons).map(([key, name]) => <option key={key} value={key}>{name}</option>)}
      </select></label>
    </div>
    {error && <p role="alert">{error}</p>}
    {org && <Findings key={[org, reason, sort].join("/")} org={org} reason={reason} sort={sort}
      toggleSort={() => setSort(sort === "value" ? "-value" : "value")} />}
  </main></>;
}

createRoot(document.getElementById("root")).render(<App />);
