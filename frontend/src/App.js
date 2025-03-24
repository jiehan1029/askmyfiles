import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [query, setQuery] = useState('');
  const [directory, setDirectory] = useState('');
  const [results, setResults] = useState([]);

  const handleSearch = async (e) => {
    e.preventDefault();

    try {
      const response = await axios.post('http://localhost:8000/search/', {
        query: query,
        directory: directory
      });
      setResults(response.data.documents);
    } catch (error) {
      console.error('Error during search:', error);
    }
  };

  return (
    <div className="App">
      <h1 className="text-center text-3xl">Local Document Search WIP</h1>
      <form onSubmit={handleSearch} className="m-4">
        <div>
          <label htmlFor="directory">Root Directory</label>
          <input
            type="text"
            id="directory"
            value={directory}
            onChange={(e) => setDirectory(e.target.value)}
            className="border p-2 m-2"
          />
        </div>
        <div>
          <label htmlFor="query">Search Query</label>
          <input
            type="text"
            id="query"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="border p-2 m-2"
          />
        </div>
        <button type="submit" className="bg-blue-500 text-white p-2">Search</button>
      </form>

      <div className="search-results">
        {results.map((doc, index) => (
          <div key={index} className="result-item">
            <p>{doc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
