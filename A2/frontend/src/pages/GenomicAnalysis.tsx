import { useState, useEffect } from 'react';
import PrimerDesigner from './PrimerDesigner';
import NCBIDownloader from './NCBIDownloader';
import SequenceAnalyzer from './SequenceAnalyzer';

interface Gene {
  id: number;
  symbol: string;
  name: string;
  ncbi_id: string;
  chromosome: string;
}

interface GenomicAnalysisProps {
  apiUrl: string;
  onGeneSelect: (geneId: number) => void;
}

export default function GenomicAnalysis({ apiUrl, onGeneSelect }: GenomicAnalysisProps) {
  const [genes, setGenes] = useState<Gene[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState<'genes' | 'sequences' | 'tools'>('genes');
  const [openTool, setOpenTool] = useState<string | null>(null);

  useEffect(() => {
    fetchGenes();
  }, []);

  const fetchGenes = async () => {
    try {
      setLoading(true);
      // Demo genes (A3)
      const demoGenes: Gene[] = [
        {
          id: 1,
          symbol: 'BRCA1',
          name: 'Breast Cancer Type 1 Susceptibility Protein',
          ncbi_id: '672',
          chromosome: '17',
        },
        {
          id: 2,
          symbol: 'BRCA2',
          name: 'Breast Cancer Type 2 Susceptibility Protein',
          ncbi_id: '675',
          chromosome: '13',
        },
        {
          id: 3,
          symbol: 'TP53',
          name: 'Tumor Protein 53',
          ncbi_id: '7157',
          chromosome: '17',
        },
        {
          id: 4,
          symbol: 'PTEN',
          name: 'Phosphatase and Tensin Homolog',
          ncbi_id: '5728',
          chromosome: '10',
        },
        {
          id: 5,
          symbol: 'MLH1',
          name: 'MutL Homolog 1',
          ncbi_id: '4292',
          chromosome: '3',
        },
      ];
      setGenes(demoGenes);
    } catch (err) {
      console.error('Error fetching genes:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="genomic-analysis-container">
      <div className="page-header">
        <h2>🧬 Genomic Analysis (A3)</h2>
        <p>DNA sequences, genes, and advanced bioinformatics tools</p>
      </div>

      <div className="section-tabs">
        <button
          className={`section-tab ${activeSection === 'genes' ? 'active' : ''}`}
          onClick={() => setActiveSection('genes')}
        >
          👨‍🔬 Genes
        </button>
        <button
          className={`section-tab ${activeSection === 'tools' ? 'active' : ''}`}
          onClick={() => setActiveSection('tools')}
        >
          🔧 Analysis Tools
        </button>
      </div>

      {activeSection === 'genes' && (
        <div className="section-content">
          <h3>Gene Database</h3>
          <p className="section-description">
            Curated list of clinically relevant genes integrated with NCBI reference data.
          </p>

          {loading ? (
            <div className="loading">Loading genes...</div>
          ) : (
            <div className="genes-table-container">
              <table className="genes-table">
                <thead>
                  <tr>
                    <th>Gene Symbol</th>
                    <th>Gene Name</th>
                    <th>NCBI ID</th>
                    <th>Chromosome</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {genes.map(gene => (
                    <tr key={gene.id}>
                      <td className="gene-symbol">
                        <strong>{gene.symbol}</strong>
                      </td>
                      <td className="gene-name">{gene.name}</td>
                      <td className="ncbi-id">{gene.ncbi_id}</td>
                      <td className="chromosome">Chr {gene.chromosome}</td>
                      <td>
                        <button
                          className="action-btn"
                          onClick={() => onGeneSelect(gene.id)}
                        >
                          View Sequences
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <div className="gene-info">
            <div className="info-box">
              <h4>📚 Reference Information</h4>
              <p>Genes are integrated with NCBI Entrez for current annotations and sequence data.</p>
            </div>
          </div>
        </div>
      )}

    

      {activeSection === 'tools' && (
        <div className="section-content">
          <h3>Bioinformatics Tools</h3>
          <p className="section-description">
            Advanced analysis tools for sequence processing and variant detection.
          </p>

          <div className="tools-grid">
            <div className="tool-card">
              <div className="tool-icon">🧪</div>
              <h4>Primer Design</h4>
              <p>Design PCR primers with melting temperature (Tm) calculation using Wallace's rule</p>
              <ul className="tool-features">
                <li>✓ Forward & reverse primer generation</li>
                <li>✓ Tm calculation</li>
                <li>✓ GC content optimization</li>
                <li>✓ Region targeting</li>
              </ul>
              <button 
                 className="btn-secondary"
                 onClick={() => setOpenTool('primer')}
              >
                 Open Tool
              </button>
            </div>

          

            <div className="tool-card">
              <div className="tool-icon">📊</div>
              <h4>Sequence Analysis</h4>
              <p>Analyze sequence composition and properties</p>
              <ul className="tool-features">
                <li>✓ GC content calculation</li>
                <li>✓ Reverse complement</li>
                <li>✓ Composition analysis</li>
                <li>✓ ORF detection</li>
              </ul>
              <button 
                className="btn-secondary"
                onClick={() => setOpenTool('sequence-analysis')}
              >
                Open Tool
              </button>
            </div>

            <div className="tool-card">
              <div className="tool-icon">🌐</div>
              <h4>NCBI Integration</h4>
              <p>Download sequences from NCBI Entrez database</p>
              <ul className="tool-features">
                <li>✓ Nucleotide database access</li>
                <li>✓ Protein database access</li>
                <li>✓ Batch downloads</li>
                <li>✓ Auto-GenBank parsing</li>
              </ul>
              <button 
                className="btn-secondary"
                onClick={() => setOpenTool('ncbi')}
              >
                Open Tool
              </button>
            </div>

          </div>
        </div>
      )}

      {/* Primer Designer Modal */}
      {openTool === 'primer' && (
        <div className="tool-modal">
          <div className="modal-content">
            <button
              className="modal-close"
              onClick={() => setOpenTool(null)}
            >
              ✕ Close
            </button>
            <PrimerDesigner apiUrl={apiUrl} />
          </div>
        </div>
      )}

      {/* NCBI Downloader Modal */}
      {openTool === 'ncbi' && (
        <div className="tool-modal">
          <div className="modal-content">
            <button
              className="modal-close"
              onClick={() => setOpenTool(null)}
            >
              ✕ Close
            </button>
            <NCBIDownloader apiUrl={apiUrl} />
          </div>
        </div>
      )}

      {/* Sequence Analysis Modal */}
      {openTool === 'sequence-analysis' && (
        <div className="tool-modal">
          <div className="modal-content">
            <button
              className="modal-close"
              onClick={() => setOpenTool(null)}
            >
              ✕ Close
            </button>
            <SequenceAnalyzer apiUrl={apiUrl} />
          </div>
        </div>
      )}
    </div>
  );
}
