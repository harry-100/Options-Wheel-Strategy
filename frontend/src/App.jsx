import React, { useState } from "react";
import axios from "axios";

const App = () => {
  // ======== UI & filter state ========
  const [tickers, setTickers] = useState("AAPL,MSFT"); // accept comma‑separated symbols
  const [minRoi, setMinRoi] = useState(0.5);
  const [minDte, setMinDte] = useState(7);
  const [maxDte, setMaxDte] = useState(45);
  const [maxIdeas, setMaxIdeas] = useState(10);

  // ======== table & sort state ========
  const [cspData, setCspData] = useState([]);
  const [ccData, setCcData] = useState([]);
  const [cspSortKey, setCspSortKey] = useState(null);
  const [cspSortAsc, setCspSortAsc] = useState(true);
  const [ccSortKey, setCcSortKey] = useState(null);
  const [ccSortAsc, setCcSortAsc] = useState(true);
  const [loading, setLoading] = useState(false);

  // ======== fetch logic ========
  const fetchData = async () => {
    setLoading(true);
    const symbols = tickers
      .split(",")
      .map((s) => s.trim().toUpperCase())
      .filter(Boolean);

    try {
      // build all API calls for CSP & CC
      const cspPromises = symbols.map((sym) =>
        axios.get(
          `http://localhost:8000/api/strategy/csp/polygon?ticker=${sym}&min_roi=${minRoi}&min_dte=${minDte}&max_dte=${maxDte}`
        )
      );
      const ccPromises = symbols.map((sym) =>
        axios.get(
          `http://localhost:8000/api/strategy/cc/polygon?ticker=${sym}&min_roi=${minRoi}&min_dte=${minDte}&max_dte=${maxDte}`
        )
      );

      const cspResults = await Promise.all(cspPromises);
      const ccResults = await Promise.all(ccPromises);

      // flatten arrays and add ticker field
      const cspMerged = cspResults.flatMap((res, idx) =>
        res.data.map((row) => ({ ticker: symbols[idx], ...row }))
      );
      const ccMerged = ccResults.flatMap((res, idx) =>
        res.data.map((row) => ({ ticker: symbols[idx], ...row }))
      );

      setCspData(cspMerged);
      setCcData(ccMerged);
    } catch (err) {
      console.error("Error fetching data:", err);
    } finally {
      setLoading(false);
    }
  };

  // ======== reusable table component ========
  const renderTable = (
    data,
    title,
    sortKey,
    sortAsc,
    setSortKey,
    setSortAsc
  ) => {
    if (!data.length)
      return <p className="text-gray-500 mt-6">No {title} data available.</p>;

    const handleSort = (key) => {
      if (sortKey === key) {
        setSortAsc(!sortAsc);
      } else {
        setSortKey(key);
        setSortAsc(true);
      }
    };

    const sorted = [...data]
      .sort((a, b) => {
        if (!sortKey) return 0;
        const aVal = a[sortKey];
        const bVal = b[sortKey];
        if (typeof aVal === "number" && typeof bVal === "number") {
          return sortAsc ? aVal - bVal : bVal - aVal;
        }
        return sortAsc
          ? String(aVal).localeCompare(String(bVal))
          : String(bVal).localeCompare(String(aVal));
      })
      .slice(0, maxIdeas);

    return (
      <div className="mt-6">
        <h2 className="text-xl font-semibold mb-2">{title}</h2>
        <table className="table-auto w-full border border-gray-400 rounded">
          <thead className="bg-gray-100">
            <tr>
              {Object.keys(sorted[0]).map((key) => (
                <th
                  key={key}
                  className={`px-4 py-2 border border-gray-400 text-left cursor-pointer ${
                    sortKey === key ? "bg-blue-100" : ""
                  }`}
                  onClick={() => handleSort(key)}
                >
                  {key} {sortKey === key ? (sortAsc ? "▲" : "▼") : ""}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((row, idx) => (
              <tr key={idx} className="border-t">
                {Object.entries(row).map(([key, val]) => (
                  <td
                    key={key}
                    className={`px-4 py-2 border border-gray-300 ${
                      sortKey === key ? "bg-blue-200" : ""
                    }`}
                  >
                    {typeof val === "number"
                      ? key === "dte"
                        ? val.toFixed(0)
                        : val.toFixed(2)
                      : val}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  // ======== UI ========
  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold text-blue-700 mb-4">
        🛞 Wheel Strategy Dashboard
      </h1>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Tickers (comma‑sep)
          </label>
          <input
            className="border p-2 rounded w-full"
            type="text"
            value={tickers}
            onChange={(e) => setTickers(e.target.value)}
            placeholder="AAPL,MSFT,QQQ"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min ROI %
          </label>
          <input
            className="border p-2 rounded w-full"
            type="number"
            value={minRoi}
            onChange={(e) => setMinRoi(parseFloat(e.target.value))}
            step="0.1"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Min DTE
          </label>
          <input
            className="border p-2 rounded w-full"
            type="number"
            value={minDte}
            onChange={(e) => setMinDte(parseInt(e.target.value))}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Max DTE
          </label>
          <input
            className="border p-2 rounded w-full"
            type="number"
            value={maxDte}
            onChange={(e) => setMaxDte(parseInt(e.target.value))}
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            # of Ideas
          </label>
          <input
            className="border p-2 rounded w-full"
            type="number"
            value={maxIdeas}
            onChange={(e) => setMaxIdeas(parseInt(e.target.value))}
            min="1"
          />
        </div>
      </div>
      <button
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        onClick={fetchData}
      >
        Search
      </button>

      {loading ? (
        <p className="mt-6 text-gray-600">Loading...</p>
      ) : (
        <>
          {renderTable(
            cspData,
            "Cash-Secured Put Ideas",
            cspSortKey,
            cspSortAsc,
            setCspSortKey,
            setCspSortAsc
          )}
          {renderTable(
            ccData,
            "Covered Call Ideas",
            ccSortKey,
            ccSortAsc,
            setCcSortKey,
            setCcSortAsc
          )}
        </>
      )}
    </div>
  );
};

export default App;
