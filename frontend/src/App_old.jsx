import React, { useState } from "react";
import axios from "axios";

const App = () => {
  const [maxIdeas, setMaxIdeas] = useState(10);
  const [cspSortKey, setCspSortKey] = useState(null);
  const [cspSortAsc, setCspSortAsc] = useState(true);
  const [ccSortKey, setCcSortKey] = useState(null);
  const [ccSortAsc, setCcSortAsc] = useState(true);
  const [ticker, setTicker] = useState("AAPL");
  const [minRoi, setMinRoi] = useState(0.5);
  const [minDte, setMinDte] = useState(7);
  const [maxDte, setMaxDte] = useState(45);
  const [cspData, setCspData] = useState([]);
  const [ccData, setCcData] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [cspRes, ccRes] = await Promise.all([
        axios.get(
          `http://localhost:8000/api/strategy/csp?ticker=${ticker}&min_roi=${minRoi}&min_dte=${minDte}&max_dte=${maxDte}`
        ),
        axios.get(
          `http://localhost:8000/api/strategy/cc?ticker=${ticker}&min_roi=${minRoi}&min_dte=${minDte}&max_dte=${maxDte}`
        ),
      ]);
      setCspData(cspRes.data);
      setCcData(ccRes.data);
    } catch (err) {
      console.error("Error fetching data:", err);
    } finally {
      setLoading(false);
    }
  };

  const renderTable = (
    data,
    title,
    sortKey,
    sortAsc,
    setSortKey,
    setSortAsc
  ) => {
    const handleSort = (key) => {
      if (sortKey === key) {
        setSortAsc(!sortAsc);
      } else {
        setSortKey(key);
        setSortAsc(true);
      }
    };

    const sortedData = [...data]
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
        {sortedData.length > 0 ? (
          <table className="table-auto w-full border border-gray-400 rounded">
            <thead className="bg-gray-100">
              <tr>
                {Object.keys(sortedData[0]).map((key) => (
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
              {sortedData.map((row, idx) => (
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
        ) : (
          <p className="text-gray-500">No {title} data available.</p>
        )}
      </div>
    );
  };

  return (
    <div className="p-4">
      <h1 className="text-2xl font-bold text-blue-700 mb-4">
        🛞 Wheel Strategy Dashboard
      </h1>
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Ticker
          </label>
          <input
            className="border p-2 rounded w-full"
            type="text"
            value={ticker}
            onChange={(e) => setTicker(e.target.value.toUpperCase())}
            placeholder="AAPL"
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
