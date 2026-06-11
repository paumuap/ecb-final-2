import { useState } from 'react';

interface Patient {
  id: number;
  patient_id: number;
  patient_name: string;
  age: number;
  sex: string;
  diagnosis: string;
  date: string;
  status: string;
  bmi?: number;
  systolic_bp?: number;
  diastolic_bp?: number;
  glucose?: number;
  cholesterol?: number;
  creatinine?: number;
  diabetes?: number;
  hypertension?: number;
  readmission_30d?: number;
  mortality?: number;
}

interface GenomicSequence {
  id: number;
  gene_symbol: string;
  accession: string;
  gc_fraction: number;
  length: number;
}

interface PatientDetailsProps {
  patient: Patient;
  apiUrlA2: string;
  apiUrlA3: string;
  token: string;
}

export default function PatientDetails({
  patient,
  apiUrlA2,
  apiUrlA3,
  token,
}: PatientDetailsProps) {
  const [activeTab, setActiveTab] = useState<'clinical' | 'genomic'>('clinical');
  
  // Map diagnosis to likely associated genes for demonstration
  const diagnosisGeneMap: { [key: string]: Array<{ symbol: string; accession: string; gc: number; length: number }> } = {
    'Sepsis': [
      { symbol: 'TNF', accession: 'NM_000594', gc: 0.52, length: 1643 },
      { symbol: 'IL6', accession: 'NM_000600', gc: 0.48, length: 2175 },
    ],
    'Normal': [],
    'Heart Failure': [
      { symbol: 'MYBPC3', accession: 'NM_000256', gc: 0.51, length: 3642 },
      { symbol: 'MYH7', accession: 'NM_000257', gc: 0.49, length: 5836 },
      { symbol: 'TNNT2', accession: 'NM_001001', gc: 0.53, length: 1623 },
    ],
    'Pneumonia': [
      { symbol: 'TLR4', accession: 'NM_003266', gc: 0.54, length: 2822 },
      { symbol: 'CD14', accession: 'NM_000591', gc: 0.50, length: 1764 },
    ],
  };

  const sequences: GenomicSequence[] = (diagnosisGeneMap[patient.diagnosis] || []).map((gene, idx) => ({
    id: idx + 1,
    gene_symbol: gene.symbol,
    accession: gene.accession,
    gc_fraction: gene.gc,
    length: gene.length,
  }));

  const getMedicalHistory = () => {
    const conditions = [];
    if (patient.diabetes) conditions.push('Type 2 Diabetes');
    if (patient.hypertension) conditions.push('Hypertension');
    if (patient.readmission_30d) conditions.push('Recent Readmission (within 30 days)');
    
    if (conditions.length === 0) {
      return 'No significant comorbidities recorded.';
    }
    return `Patient has the following conditions: ${conditions.join(', ')}.`;
  };

  return (
    <div className="patient-details-container">
      <div className="patient-header">
        <div className="patient-card">
          <h2>👤 {patient.patient_name} (ID: {patient.patient_id})</h2>
          <div className="patient-meta">
            <div className="meta-item">
              <span className="label">Age:</span>
              <span className="value">{patient.age} years</span>
            </div>
            <div className="meta-item">
              <span className="label">Gender:</span>
              <span className="value">{patient.sex}</span>
            </div>
            <div className="meta-item">
              <span className="label">Diagnosis:</span>
              <span className="value">{patient.diagnosis}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="tab-navigation">
        <button
          className={`tab-btn ${activeTab === 'clinical' ? 'active' : ''}`}
          onClick={() => setActiveTab('clinical')}
        >
          📋 Clinical Data (A2)
        </button>
        <button
          className={`tab-btn ${activeTab === 'genomic' ? 'active' : ''}`}
          onClick={() => setActiveTab('genomic')}
        >
          🧬 Genomic Data (A3)
        </button>
      </div>

      {activeTab === 'clinical' && (
        <div className="tab-content">
          <h3>📊 Vital Signs & Labs</h3>
          <div className="features-grid">
            <div className="feature-card">
              <h4>BP</h4>
              <p>{patient.systolic_bp || 'N/A'} / {patient.diastolic_bp || 'N/A'} mmHg</p>
            </div>
            <div className="feature-card">
              <h4>Glucose</h4>
              <p>{patient.glucose?.toFixed(1) || 'N/A'} mg/dL</p>
            </div>
            <div className="feature-card">
              <h4>Cholesterol</h4>
              <p>{patient.cholesterol?.toFixed(1) || 'N/A'} mg/dL</p>
            </div>
            <div className="feature-card">
              <h4>Creatinine</h4>
              <p>{patient.creatinine?.toFixed(2) || 'N/A'} mg/dL</p>
            </div>
            <div className="feature-card">
              <h4>BMI</h4>
              <p>{patient.bmi?.toFixed(1) || 'N/A'} kg/m²</p>
            </div>
            <div className="feature-card">
              <h4>Status</h4>
              <p>{patient.status}</p>
            </div>
          </div>

          <h3>Medical History</h3>
          <div className="history-box">{getMedicalHistory()}</div>

          <h3>Clinical Recommendations</h3>
          <div className="recommendations">
            <div className="rec-item">
              <span className="rec-icon">✅</span>
              <span>Regular monitoring of vital signs required</span>
            </div>
            <div className="rec-item">
              <span className="rec-icon">✅</span>
              <span>Follow-up appointments based on diagnosis</span>
            </div>
            <div className="rec-item">
              <span className="rec-icon">✅</span>
              <span>Genetic counseling recommended</span>
            </div>
            <div className="rec-item">
              <span className="rec-icon">✅</span>
              <span>Family screening as appropriate</span>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'genomic' && (
        <div className="tab-content">
          <h3>🧬 Associated DNA Sequences</h3>

          {sequences.length > 0 ? (
            <div className="sequences-grid">
              {sequences.map(seq => (
                <div key={seq.id} className="sequence-card">
                  <div className="seq-header">
                    <h4>{seq.gene_symbol}</h4>
                    <span className="accession">{seq.accession}</span>
                  </div>

                  <div className="seq-details">
                    <div className="detail">
                      <span className="detail-label">Length:</span>
                      <span className="detail-value">{seq.length} bp</span>
                    </div>
                    <div className="detail">
                      <span className="detail-label">GC Content:</span>
                      <span className="detail-value">{(seq.gc_fraction * 100).toFixed(1)}%</span>
                    </div>
                  </div>

                  <div className="gc-progress">
                    <div
                      className="gc-bar"
                      style={{ width: `${seq.gc_fraction * 100}%` }}
                    ></div>
                  </div>

                  <div className="seq-actions">
                    <button className="btn-small">Analyze</button>
                    <button className="btn-small">Design Primers</button>
                    <button className="btn-small">View Sequence</button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-data">No specific genomic sequences associated with {patient.diagnosis}</div>
          )}

          <h3>Upload New Sequence</h3>
          <div className="upload-section">
            <input
              type="file"
              accept=".fasta,.fa,.fna,.gb,.gbk"
              className="file-input"
            />
            <button className="btn-primary">Upload FASTA/GenBank</button>
          </div>
        </div>
      )}

    </div>
  );
}
