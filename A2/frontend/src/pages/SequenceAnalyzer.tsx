import { useState } from 'react';

interface AnalysisResult {
  gc_fraction: number;
  reverse_complement: string;
  composition: {
    A: number;
    T: number;
    G: number;
    C: number;
  };
  composition_percent: {
    A: number;
    T: number;
    G: number;
    C: number;
  };
  length: number;
}

interface SequenceAnalyzerProps {
  apiUrl: string;
}

export default function SequenceAnalyzer({ apiUrl }: SequenceAnalyzerProps) {
  const [sequenceInput, setSequenceInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState<AnalysisResult | null>(null);

  const analyzeSequence = async () => {
    setError('');
    setLoading(true);
    setResults(null);

    try {
      const seq = sequenceInput.replace(/\r\n/g, '').replace(/\n/g, '').replace(/\r/g, '').trim().toUpperCase();

      if (seq.length === 0) {
        setError('Please enter a sequence');
        setLoading(false);
        return;
      }

      // Validate DNA sequence (only ATGC and N)
      if (!/^[ATGCN]+$/.test(seq)) {
        setError('Invalid sequence. Only ATGC and N characters are allowed.');
        setLoading(false);
        return;
      }

      // Try to use API if available, otherwise fall back to local calculation
      try {
        const response = await fetch('/dna-api/sequences/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sequence: seq }),
        });

        if (response.ok) {
          const data = await response.json();
          setResults(data);
        } else {
          // Fall back to local analysis
          analyzeLocal(seq);
        }
      } catch {
        // API not available, use local analysis
        analyzeLocal(seq);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const analyzeLocal = (seq: string) => {
    // Calculate GC fraction
    const g = (seq.match(/G/g) || []).length;
    const c = (seq.match(/C/g) || []).length;
    const gc_fraction = (g + c) / seq.length;

    // Calculate reverse complement
    const complement: { [key: string]: string } = {
      A: 'T',
      T: 'A',
      G: 'C',
      C: 'G',
      N: 'N',
    };
    const reverse_complement = seq
      .split('')
      .reverse()
      .map(base => complement[base] || 'N')
      .join('');

    // Calculate composition
    const a = (seq.match(/A/g) || []).length;
    const t = (seq.match(/T/g) || []).length;

    const composition = { A: a, T: t, G: g, C: c };
    const composition_percent = {
      A: (a / seq.length) * 100,
      T: (t / seq.length) * 100,
      G: (g / seq.length) * 100,
      C: (c / seq.length) * 100,
    };

    setResults({
      gc_fraction,
      reverse_complement,
      composition,
      composition_percent,
      length: seq.length,
    });
  };

  return (
    <div className="sequence-analyzer-container">
      <div className="page-header">
        <h2>📊 Sequence Analysis Tool</h2>
        <p>Analyze composition and properties of DNA sequences</p>
      </div>

      <div className="analyzer-layout">
        {/* Input Section */}
        <div className="input-section">
          <div className="form-group">
            <label>DNA Sequence</label>
            <textarea
              value={sequenceInput}
              onChange={(e) => setSequenceInput(e.target.value.toUpperCase())}
              placeholder="Paste or type DNA sequence (ATGC)..."
              rows={8}
              className="sequence-input"
            />
            <div className="sequence-stats">
              <span>Length: {sequenceInput.length} bp</span>
              {sequenceInput.length > 0 && (
                <>
                  <span>
                    GC%:{' '}
                    {(
                      (((sequenceInput.match(/G/gi) || []).length +
                        (sequenceInput.match(/C/gi) || []).length) /
                        sequenceInput.length) *
                      100
                    ).toFixed(1)}%
                  </span>
                </>
              )}
            </div>
          </div>

          <div className="button-group">
            <button
              onClick={analyzeSequence}
              disabled={loading || sequenceInput.length === 0}
              className="btn-primary"
            >
              {loading ? '⏳ Analyzing...' : '🔬 Analyze Sequence'}
            </button>
          </div>

          {error && <div className="error">{error}</div>}
        </div>

        {/* Results Section */}
        {results && (
          <div className="results-section">
            <h3>📈 Analysis Results</h3>

            {/* Summary Cards */}
            <div className="results-grid">
              <div className="result-card">
                <h4>Sequence Length</h4>
                <p className="result-value">{results.length} bp</p>
              </div>

              <div className="result-card highlight">
                <h4>GC Content</h4>
                <p className="result-value">{(results.gc_fraction * 100).toFixed(1)}%</p>
                <small>
                  {results.composition.G} G + {results.composition.C} C = {results.composition.G + results.composition.C}
                </small>
              </div>

              <div className="result-card">
                <h4>AT Content</h4>
                <p className="result-value">
                  {((1 - results.gc_fraction) * 100).toFixed(1)}%
                </p>
                <small>
                  {results.composition.A} A + {results.composition.T} T = {results.composition.A + results.composition.T}
                </small>
              </div>
            </div>

            {/* Composition Analysis */}
            <div className="composition-section">
              <h4>📊 Nucleotide Composition</h4>
              <div className="composition-grid">
                {Object.entries(results.composition).map(([base, count]) => (
                  <div key={base} className="composition-bar">
                    <div className="bar-label">
                      <span className={`base-letter ${base.toLowerCase()}`}>{base}</span>
                      <span className="bar-value">
                        {count} ({results.composition_percent[base as keyof typeof results.composition_percent].toFixed(1)}%)
                      </span>
                    </div>
                    <div className="bar-container">
                      <div
                        className={`bar-fill ${base.toLowerCase()}`}
                        style={{
                          width: `${(results.composition_percent[base as keyof typeof results.composition_percent] / 100) * 100}%`,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              {/* Composition Table */}
              <table className="composition-table">
                <thead>
                  <tr>
                    <th>Base</th>
                    <th>Count</th>
                    <th>Percentage</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(results.composition).map(([base, count]) => (
                    <tr key={base}>
                      <td className={`base-cell ${base.toLowerCase()}`}><strong>{base}</strong></td>
                      <td>{count}</td>
                      <td>{results.composition_percent[base as keyof typeof results.composition_percent].toFixed(2)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Reverse Complement */}
            <div className="reverse-complement-section">
              <h4>↔️ Reverse Complement</h4>
              <div className="sequence-display">
                <div className="original">
                  <span className="label">Original (5' → 3'):</span>
                  <code>{sequenceInput}</code>
                  <button
                    className="btn-small"
                    onClick={() => navigator.clipboard.writeText(sequenceInput)}
                  >
                    📋 Copy
                  </button>
                </div>
                <div className="complement">
                  <span className="label">Reverse Complement (3' → 5'):</span>
                  <code>{results.reverse_complement}</code>
                  <button
                    className="btn-small"
                    onClick={() => navigator.clipboard.writeText(results.reverse_complement)}
                  >
                    📋 Copy
                  </button>
                </div>
              </div>
            </div>

            {/* Information Box */}
            <div className="info-box">
              <h4>💡 About the Analysis</h4>
              <ul>
                <li><strong>GC Content:</strong> Percentage of Guanine and Cytosine nucleotides. Important for DNA stability.</li>
                <li><strong>Reverse Complement:</strong> The complementary strand read in reverse direction (3'→5'). Essential for understanding double-stranded DNA.</li>
                <li><strong>Composition:</strong> Count and percentage of each nucleotide base (A, T, G, C).</li>
                <li><strong>DNA Stability:</strong> Higher GC content generally means more stable DNA (3 hydrogen bonds vs 2 for AT).</li>
              </ul>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
