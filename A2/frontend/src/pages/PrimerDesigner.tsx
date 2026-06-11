import { useState } from 'react';

interface PrimerPair {
  forward_primer: string;
  reverse_primer: string;
  forward_tm: number;
  reverse_tm: number;
  forward_gc: number;
  reverse_gc: number;
  tm_diff: number;
  quality_score: number;
  forward_position: number;
  reverse_position: number;
}

interface PrimerDesignerProps {
  apiUrl: string;
}

export default function PrimerDesigner({ apiUrl }: PrimerDesignerProps) {
  const [sequenceInput, setSequenceInput] = useState('');
  const [targetStart, setTargetStart] = useState(0);
  const [targetEnd, setTargetEnd] = useState(100);
  const [primerLength, setPrimerLength] = useState(20);
  const [minGC, setMinGC] = useState(40);
  const [maxGC, setMaxGC] = useState(60);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [results, setResults] = useState<PrimerPair[]>([]);
  const [selectedPair, setSelectedPair] = useState<PrimerPair | null>(null);

  // Calculate Tm using Wallace's rule: Tm = 4(G+C) + 2(A+T)
  const calculateTm = (primer: string): number => {
    const g = (primer.match(/G/gi) || []).length;
    const c = (primer.match(/C/gi) || []).length;
    const a = (primer.match(/A/gi) || []).length;
    const t = (primer.match(/T/gi) || []).length;
    return 4 * (g + c) + 2 * (a + t);
  };

  // Calculate GC content
  const calculateGC = (primer: string): number => {
    const g = (primer.match(/G/gi) || []).length;
    const c = (primer.match(/C/gi) || []).length;
    return ((g + c) / primer.length) * 100;
  };

  // Reverse complement (for reverse primer)
  const reverseComplement = (seq: string): string => {
    const complement: { [key: string]: string } = {
      A: 'T',
      T: 'A',
      G: 'C',
      C: 'G',
      N: 'N',
    };
    return seq
      .toUpperCase()
      .split('')
      .reverse()
      .map(base => complement[base] || 'N')
      .join('');
  };

  // Quality score: 100 = perfect (GC 50%, Tm diff 0), decreases based on deviation
  const calculateQualityScore = (
    fwdTm: number,
    revTm: number,
    fwdGC: number,
    revGC: number
  ): number => {
    let score = 100;
    
    // Penalize Tm difference (should be < 5°C for good PCR)
    const tmDiff = Math.abs(fwdTm - revTm);
    score -= Math.min(50, tmDiff * 5);
    
    // Penalize GC deviation from ideal (50%)
    const fwdGCDev = Math.abs(fwdGC - 50);
    const revGCDev = Math.abs(revGC - 50);
    score -= Math.min(30, (fwdGCDev + revGCDev) / 2);
    
    // Penalize Tm outside ideal range (55-65°C)
    if (fwdTm < 55 || fwdTm > 65) score -= 15;
    if (revTm < 55 || revTm > 65) score -= 15;
    
    return Math.max(0, score);
  };

  // Design primers locally with multiple candidates
  const designPrimersLocal = async () => {
    setError('');
    setLoading(true);
    setResults([]);
    setSelectedPair(null);

    try {
      const seq = sequenceInput.toUpperCase();

      if (seq.length === 0) {
        setError('Please enter a sequence');
        setLoading(false);
        return;
      }

      if (targetStart < 0 || targetEnd > seq.length || targetStart >= targetEnd) {
        setError('Invalid target region coordinates');
        setLoading(false);
        return;
      }

      const targetSeq = seq.substring(targetStart, targetEnd);

      if (targetSeq.length < primerLength * 2) {
        setError(`Target region must be at least ${primerLength * 2} bp for primer pair design`);
        setLoading(false);
        return;
      }

      const candidates: PrimerPair[] = [];
      const maxCandidates = Math.min(10, Math.floor(targetSeq.length / primerLength));

      // Generate multiple primer pairs across the target region
      for (let i = 0; i < maxCandidates; i++) {
        const step = Math.floor(targetSeq.length / maxCandidates);
        const fwdPos = i * step;
        const revPos = Math.max(fwdPos + primerLength, targetSeq.length - primerLength - (i * 2));

        if (fwdPos + primerLength > targetSeq.length || revPos + primerLength > targetSeq.length) {
          continue;
        }

        const forwardSeq = targetSeq.substring(fwdPos, fwdPos + primerLength);
        const revSeq = targetSeq.substring(revPos, revPos + primerLength);
        const reversePrimer = reverseComplement(revSeq);

        const fwdTm = calculateTm(forwardSeq);
        const revTm = calculateTm(reversePrimer);
        const fwdGC = calculateGC(forwardSeq);
        const revGC = calculateGC(reversePrimer);
        const tmDiff = Math.abs(fwdTm - revTm);

        // Filter by GC content constraints
        if (fwdGC < minGC || fwdGC > maxGC || revGC < minGC || revGC > maxGC) {
          continue;
        }

        candidates.push({
          forward_primer: forwardSeq,
          reverse_primer: reversePrimer,
          forward_tm: fwdTm,
          reverse_tm: revTm,
          forward_gc: fwdGC,
          reverse_gc: revGC,
          tm_diff: tmDiff,
          quality_score: calculateQualityScore(fwdTm, revTm, fwdGC, revGC),
          forward_position: targetStart + fwdPos,
          reverse_position: targetStart + revPos,
        });
      }

      if (candidates.length === 0) {
        setError('No primer pairs met the criteria. Try adjusting GC content range or primer length.');
        setLoading(false);
        return;
      }

      // Sort by quality score (descending)
      candidates.sort((a, b) => b.quality_score - a.quality_score);
      setResults(candidates);
      setSelectedPair(candidates[0]); // Select best pair by default

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="primer-designer-container">
      <div className="page-header">
        <h2>🧪 Primer Designer</h2>
        <p>Design forward and reverse primers for PCR amplification</p>
      </div>

      <div className="designer-layout">
        {/* Input Section */}
        <div className="input-section">
          <div className="form-group">
            <label>DNA Sequence</label>
            <textarea
              value={sequenceInput}
              onChange={(e) => setSequenceInput(e.target.value.toUpperCase())}
              placeholder="Paste DNA sequence (ATCG)..."
              rows={6}
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

          <div className="params-grid">
            <div className="form-group">
              <label>Primer Length (bp)</label>
              <input
                type="number"
                value={primerLength}
                onChange={(e) => setPrimerLength(Math.max(15, Math.min(35, parseInt(e.target.value) || 20)))}
                min="15"
                max="35"
              />
              <small>Typical range: 18-25 bp</small>
            </div>

            <div className="form-group">
              <label>Target Start Position</label>
              <input
                type="number"
                value={targetStart}
                onChange={(e) => setTargetStart(Math.max(0, parseInt(e.target.value) || 0))}
                min="0"
              />
            </div>

            <div className="form-group">
              <label>Target End Position</label>
              <input
                type="number"
                value={targetEnd}
                onChange={(e) => setTargetEnd(Math.max(targetStart + 1, parseInt(e.target.value) || 100))}
                min={targetStart + 1}
              />
            </div>

            <div className="form-group">
              <label>Min GC Content (%)</label>
              <input
                type="number"
                value={minGC}
                onChange={(e) => setMinGC(Math.max(0, Math.min(50, parseInt(e.target.value) || 40)))}
                min="0"
                max="50"
              />
            </div>

            <div className="form-group">
              <label>Max GC Content (%)</label>
              <input
                type="number"
                value={maxGC}
                onChange={(e) => setMaxGC(Math.max(minGC, Math.min(100, parseInt(e.target.value) || 60)))}
                min={minGC}
                max="100"
              />
            </div>
          </div>

          <div className="button-group">
            <button
              onClick={designPrimersLocal}
              disabled={loading || sequenceInput.length === 0}
              className="btn-primary"
            >
              {loading ? '⏳ Designing...' : '🚀 Design Primer Pairs'}
            </button>
          </div>

          {error && <div className="error">{error}</div>}
        </div>

        {/* Results Section */}
        {results.length > 0 && (
          <div className="results-section">
            <h3>🎯 Primer Design Results ({results.length} candidates)</h3>

            <div className="candidates-list">
              {results.map((pair, idx) => (
                <div
                  key={idx}
                  className={`candidate-card ${selectedPair === pair ? 'selected' : ''}`}
                  onClick={() => setSelectedPair(pair)}
                >
                  <div className="candidate-header">
                    <span className="rank">#{idx + 1}</span>
                    <span className="quality-badge">{pair.quality_score.toFixed(0)} pts</span>
                  </div>
                  <div className="candidate-preview">
                    <div className="primer-mini">
                      <span className="strand">→</span>
                      <span className="seq">{pair.forward_primer}</span>
                      <span className="tm">{pair.forward_tm.toFixed(0)}°C</span>
                    </div>
                    <div className="primer-mini">
                      <span className="strand">←</span>
                      <span className="seq">{pair.reverse_primer}</span>
                      <span className="tm">{pair.reverse_tm.toFixed(0)}°C</span>
                    </div>
                  </div>
                  <div className="candidate-metrics">
                    <span>ΔTm: {pair.tm_diff.toFixed(1)}°C</span>
                    <span>FGC: {pair.forward_gc.toFixed(1)}%</span>
                    <span>RGC: {pair.reverse_gc.toFixed(1)}%</span>
                  </div>
                </div>
              ))}
            </div>

            {selectedPair && (
              <div className="selected-pair-details">
                <h3>Selected Primer Pair Details</h3>

                <div className="primer-card forward">
                  <div className="primer-header">
                    <h4>→ Forward Primer (5' → 3')</h4>
                    <span className="primer-length">{selectedPair.forward_primer.length} bp</span>
                  </div>
                  <div className="primer-sequence">
                    <code>{selectedPair.forward_primer}</code>
                  </div>
                  <div className="primer-properties">
                    <div className="property">
                      <span className="label">Tm (Wallace's rule):</span>
                      <span className="value">{selectedPair.forward_tm.toFixed(1)}°C</span>
                    </div>
                    <div className="property">
                      <span className="label">GC Content:</span>
                      <span className="value">{selectedPair.forward_gc.toFixed(1)}%</span>
                    </div>
                    <div className="property">
                      <span className="label">Position in Target:</span>
                      <span className="value">{selectedPair.forward_position}</span>
                    </div>
                    <div className="property">
                      <span className="label">Composition:</span>
                      <span className="value">
                        A:{(selectedPair.forward_primer.match(/A/g) || []).length} T:
                        {(selectedPair.forward_primer.match(/T/g) || []).length} G:
                        {(selectedPair.forward_primer.match(/G/g) || []).length} C:
                        {(selectedPair.forward_primer.match(/C/g) || []).length}
                      </span>
                    </div>
                  </div>
                  <button onClick={() => navigator.clipboard.writeText(selectedPair.forward_primer)} className="btn-small">
                    📋 Copy
                  </button>
                </div>

                <div className="primer-card reverse">
                  <div className="primer-header">
                    <h4>← Reverse Primer (5' → 3')</h4>
                    <span className="primer-length">{selectedPair.reverse_primer.length} bp</span>
                  </div>
                  <div className="primer-sequence">
                    <code>{selectedPair.reverse_primer}</code>
                  </div>
                  <div className="primer-properties">
                    <div className="property">
                      <span className="label">Tm (Wallace's rule):</span>
                      <span className="value">{selectedPair.reverse_tm.toFixed(1)}°C</span>
                    </div>
                    <div className="property">
                      <span className="label">GC Content:</span>
                      <span className="value">{selectedPair.reverse_gc.toFixed(1)}%</span>
                    </div>
                    <div className="property">
                      <span className="label">Position in Target:</span>
                      <span className="value">{selectedPair.reverse_position}</span>
                    </div>
                    <div className="property">
                      <span className="label">Composition:</span>
                      <span className="value">
                        A:{(selectedPair.reverse_primer.match(/A/g) || []).length} T:
                        {(selectedPair.reverse_primer.match(/T/g) || []).length} G:
                        {(selectedPair.reverse_primer.match(/G/g) || []).length} C:
                        {(selectedPair.reverse_primer.match(/C/g) || []).length}
                      </span>
                    </div>
                  </div>
                  <button onClick={() => navigator.clipboard.writeText(selectedPair.reverse_primer)} className="btn-small">
                    📋 Copy
                  </button>
                </div>

                <div className="pair-summary">
                  <h4>Pair Quality Summary</h4>
                  <div className="summary-grid">
                    <div className="summary-item">
                      <span className="label">Quality Score</span>
                      <span className="value">{selectedPair.quality_score.toFixed(0)}/100</span>
                    </div>
                    <div className="summary-item">
                      <span className="label">Tm Difference</span>
                      <span className={`value ${selectedPair.tm_diff < 5 ? 'good' : selectedPair.tm_diff < 10 ? 'warning' : 'poor'}`}>
                        {selectedPair.tm_diff.toFixed(1)}°C
                      </span>
                    </div>
                    <div className="summary-item">
                      <span className="label">Fwd Tm</span>
                      <span className={`value ${selectedPair.forward_tm >= 55 && selectedPair.forward_tm <= 65 ? 'good' : 'warning'}`}>
                        {selectedPair.forward_tm.toFixed(1)}°C
                      </span>
                    </div>
                    <div className="summary-item">
                      <span className="label">Rev Tm</span>
                      <span className={`value ${selectedPair.reverse_tm >= 55 && selectedPair.reverse_tm <= 65 ? 'good' : 'warning'}`}>
                        {selectedPair.reverse_tm.toFixed(1)}°C
                      </span>
                    </div>
                  </div>
                </div>

                <div className="design-guide">
                  <h4>💡 Design Quality Indicators</h4>
                  <ul>
                    <li>✅ <strong>Ideal Tm Range:</strong> 55-65°C</li>
                    <li>✅ <strong>Optimal GC Content:</strong> 40-60%</li>
                    <li>✅ <strong>Typical Primer Length:</strong> 18-25 bp</li>
                    <li>✅ <strong>Primer Pair Tm Difference:</strong> Should be &lt; 5°C for efficient PCR</li>
                    <li>
                      ℹ️ <strong>Strand Pairing:</strong> Forward = sense strand (5'→3'), Reverse = reverse complement (standard PCR)
                    </li>
                  </ul>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
