import { useState } from 'react';

interface NCBISequence {
  accession: string;
  description: string;
  organism: string;
  sequence: string;
  length: number;
  gc_percentage?: number;
}

interface NCBIDownloaderProps {
  apiUrl: string;
}

export default function NCBIDownloader({ apiUrl }: NCBIDownloaderProps) {
  const [geneSymbol, setGeneSymbol] = useState('');
  const [geneName, setGeneName] = useState('');
  const [query, setQuery] = useState('');
  const [database, setDatabase] = useState<'nucleotide' | 'protein'>('nucleotide');
  const [maxResults, setMaxResults] = useState(5);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchResults, setSearchResults] = useState<NCBISequence[]>([]);
  const [selectedSequences, setSelectedSequences] = useState<Set<string>>(new Set());

  const searchNCBI = async () => {
    setError('');
    setLoading(true);
    setSearchResults([]);
    setSelectedSequences(new Set());

    try {
      if (!query.trim()) {
        setError('Please enter a search query or accession number');
        setLoading(false);
        return;
      }

      const response = await fetch(`${apiUrl}/sequences/ncbi-download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: query.trim(),
          database,
          max_results: maxResults,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to search NCBI');
      }

      const data = await response.json();
      
      // Calculate GC percentage for display
      const resultsWithGC = data.sequences.map((seq: any) => ({
        ...seq,
        gc_percentage: seq.gc_fraction ? (seq.gc_fraction * 100).toFixed(1) : 'N/A',
      }));

      setSearchResults(resultsWithGC);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const toggleSequenceSelection = (accession: string) => {
    const newSelected = new Set(selectedSequences);
    if (newSelected.has(accession)) {
      newSelected.delete(accession);
    } else {
      newSelected.add(accession);
    }
    setSelectedSequences(newSelected);
  };

  const saveSelectedSequences = async () => {
    if (selectedSequences.size === 0) {
      setError('Please select at least one sequence to save');
      return;
    }

    if (!geneSymbol.trim()) {
      setError('Please enter a gene symbol');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const selectedSeqs = searchResults.filter(s => selectedSequences.has(s.accession));
      let successCount = 0;

      for (const seq of selectedSeqs) {
        const response = await fetch(`${apiUrl}/sequences/ncbi-download-and-save`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            gene_symbol: geneSymbol.toUpperCase(),
            gene_name: geneName || geneSymbol,
            ncbi_accession: seq.accession,
            sequence: seq.sequence,
            organism: seq.organism,
            description: seq.description,
          }),
        });

        if (response.ok) {
          successCount++;
        }
      }

      setError('');
      alert(`Successfully saved ${successCount}/${selectedSeqs.length} sequences`);
      setSelectedSequences(new Set());
      setSearchResults([]);
      setQuery('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save sequences');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="ncbi-downloader-container">
      <div className="page-header">
        <h2>🌐 NCBI Sequence Downloader</h2>
        <p>Download sequences from NCBI Entrez and persist to database</p>
      </div>

      <div className="downloader-layout">
        {/* Search Section */}
        <div className="search-section">
          <h3>Step 1: Search NCBI</h3>

          <div className="form-group">
            <label>Search Query</label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g., BRCA1 human mRNA or NM_007294"
              className="text-input"
            />
            <small>Enter gene name, accession number, or search term</small>
          </div>

          <div className="params-grid">
            <div className="form-group">
              <label>Database</label>
              <select
                value={database}
                onChange={(e) => setDatabase(e.target.value as 'nucleotide' | 'protein')}
                className="select-input"
              >
                <option value="nucleotide">Nucleotide (DNA/RNA)</option>
                <option value="protein">Protein</option>
              </select>
            </div>

            <div className="form-group">
              <label>Max Results</label>
              <input
                type="number"
                value={maxResults}
                onChange={(e) => setMaxResults(Math.max(1, Math.min(20, parseInt(e.target.value) || 5)))}
                min="1"
                max="20"
              />
            </div>
          </div>

          <button
            onClick={searchNCBI}
            disabled={loading || !query.trim()}
            className="btn-primary"
          >
            {loading ? '⏳ Searching...' : '🔍 Search NCBI'}
          </button>

          {error && <div className="error">{error}</div>}
        </div>

        {/* Results Section */}
        {searchResults.length > 0 && (
          <div className="results-section">
            <h3>Step 2: Select Sequences ({selectedSequences.size} selected)</h3>

            <div className="sequences-list">
              {searchResults.map((seq, idx) => (
                <div
                  key={idx}
                  className={`sequence-card ${selectedSequences.has(seq.accession) ? 'selected' : ''}`}
                  onClick={() => toggleSequenceSelection(seq.accession)}
                >
                  <div className="sequence-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedSequences.has(seq.accession)}
                      onChange={() => toggleSequenceSelection(seq.accession)}
                      onClick={(e) => e.stopPropagation()}
                    />
                  </div>

                  <div className="sequence-info">
                    <h4 className="accession">{seq.accession}</h4>
                    <p className="description">{seq.description}</p>
                    <div className="metadata">
                      <span className="organism">🧬 {seq.organism || 'Unknown organism'}</span>
                      <span className="length">📏 {seq.length} bp</span>
                      {seq.gc_percentage && (
                        <span className="gc-content">
                          GC: {seq.gc_percentage}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Save Section */}
        {searchResults.length > 0 && (
          <div className="save-section">
            <h3>Step 3: Save to Database</h3>

            <div className="form-group">
              <label>Gene Symbol *</label>
              <input
                type="text"
                value={geneSymbol}
                onChange={(e) => setGeneSymbol(e.target.value.toUpperCase())}
                placeholder="e.g., BRCA1"
                className="text-input"
              />
              <small>Required: gene symbol (will be created if not exists)</small>
            </div>

            <div className="form-group">
              <label>Gene Name</label>
              <input
                type="text"
                value={geneName}
                onChange={(e) => setGeneName(e.target.value)}
                placeholder="e.g., Breast Cancer Type 1 Susceptibility Protein"
                className="text-input"
              />
              <small>Optional: full gene name</small>
            </div>

            <button
              onClick={saveSelectedSequences}
              disabled={loading || selectedSequences.size === 0 || !geneSymbol.trim()}
              className="btn-primary"
            >
              {loading ? '💾 Saving...' : `💾 Save ${selectedSequences.size} Sequence(s)`}
            </button>
          </div>
        )}
      </div>

      <div className="info-box">
        <h4>📚 How to Use</h4>
        <ol>
          <li>Enter a search query (gene name, accession, or description)</li>
          <li>Select database (nucleotide for DNA/RNA, protein for amino acids)</li>
          <li>Click "Search NCBI" to retrieve results</li>
          <li>Select sequences you want to save</li>
          <li>Enter gene symbol and name</li>
          <li>Click "Save Sequences" to persist to database</li>
        </ol>

        <h4>📝 Examples</h4>
        <ul>
          <li><code>BRCA1 human mRNA</code> - Find BRCA1 mRNA sequences</li>
          <li><code>NM_007294</code> - Find specific accession</li>
          <li><code>TP53 Homo sapiens</code> - Find p53 sequences</li>
          <li><code>MYH7 heart</code> - Find myosin sequences</li>
        </ul>
      </div>
    </div>
  );
}
