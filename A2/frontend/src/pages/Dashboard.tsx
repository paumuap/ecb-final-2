import { useState, useEffect } from 'react';

interface Sample {
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

interface DashboardProps {
  onPatientSelect: (patient: Sample) => void;
  apiUrl: string;
  token: string;
  user: { id: number; username: string; email: string; role: string };
}

export default function Dashboard({ onPatientSelect, apiUrl, token, user }: DashboardProps) {
  const [samples, setSamples] = useState<Sample[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetchSamples();
  }, []);

  const fetchSamples = async () => {
    try {
      setLoading(true);
      // Load synthetic data from CSV
      const response = await fetch('/synthetic_clinical_dataset.csv');
      const csvText = await response.text();
      const lines = csvText.trim().split('\n');
      const headers = lines[0].split(',').map(h => h.trim());
      
      // Determine how many patients user can see based on role
      let maxPatients = 50;
      if (user.role === 'admin') {
        maxPatients = 50; // Admin sees all
      } else if (user.role === 'doctor') {
        maxPatients = 10; // Doctor sees assigned patients (simulated as 10)
      } else {
        maxPatients = 5; // Other roles see limited view
      }
      
      const parsedSamples: Sample[] = lines.slice(1, maxPatients + 1).map((line, index) => {
        const values = line.split(',').map(v => v.trim());
        const rowData: { [key: string]: any } = {};
        
        headers.forEach((header, idx) => {
          const value = values[idx];
          rowData[header] = isNaN(Number(value)) ? value : Number(value);
        });

        const statusOptions = ['Analyzed', 'Processing', 'Pending'];
        const status = statusOptions[index % 3];
        
        return {
          id: index + 1,
          patient_id: rowData.patient_id,
          patient_name: `Patient ${rowData.patient_id}`,
          age: rowData.age,
          sex: rowData.sex,
          diagnosis: rowData.diagnosis || 'Unknown',
          date: new Date(2024, 5, Math.max(1, (index % 30) + 1)).toISOString().split('T')[0],
          status,
          bmi: rowData.bmi,
          systolic_bp: rowData.systolic_bp,
          diastolic_bp: rowData.diastolic_bp,
          glucose: rowData.glucose,
          cholesterol: rowData.cholesterol,
          creatinine: rowData.creatinine,
          diabetes: rowData.diabetes,
          hypertension: rowData.hypertension,
          readmission_30d: rowData.readmission_30d,
          mortality: rowData.mortality,
        };
      });

      setSamples(parsedSamples);
    } catch (err) {
      console.error('Error loading synthetic data:', err);
      // Fallback to empty or minimal demo
      setSamples([]);
    } finally {
      setLoading(false);
    }
  };

  const filteredSamples = samples.filter(sample => {
    const matchesFilter = filter === 'all' || sample.status.toLowerCase() === filter.toLowerCase();
    const matchesSearch =
      sample.patient_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      sample.diagnosis.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  return (
    <div className="dashboard-container">
      <div className="page-header">
        <h2>📊 Clinical Dashboard</h2>
        <p>Patient samples with integrated genomic analysis</p>
      </div>

      <div className="role-access-info">
        <span className="role-badge">{user.role.toUpperCase()}</span>
        <span className="access-text">
          Viewing <strong>{samples.length}</strong> of <strong>50</strong> available patients
          {user.role !== 'admin' && <span className="hint"> (role-based access)</span>}
        </span>
      </div>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-number">{samples.length}</div>
          <div className="stat-label">Total Samples</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{samples.filter(s => s.status === 'Analyzed').length}</div>
          <div className="stat-label">Analyzed</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{samples.filter(s => s.status === 'Processing').length}</div>
          <div className="stat-label">Processing</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{samples.filter(s => s.status === 'Pending').length}</div>
          <div className="stat-label">Pending</div>
        </div>
      </div>

      <div className="controls-section">
        <input
          type="text"
          placeholder="🔍 Search by patient name or diagnosis..."
          className="search-input"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />

        <div className="filter-buttons">
          {['all', 'analyzed', 'processing', 'pending'].map(status => (
            <button
              key={status}
              className={`filter-btn ${filter === status ? 'active' : ''}`}
              onClick={() => setFilter(status)}
            >
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </button>
          ))}
        </div>
      </div>

      <div className="table-container">
        <table className="samples-table">
          <thead>
            <tr>
              <th>Sample ID</th>
              <th>Patient Name</th>
              <th>Diagnosis</th>
              <th>Collection Date</th>
              <th>Analysis Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredSamples.length > 0 ? (
              filteredSamples.map(sample => (
                <tr key={sample.id}>
                  <td>#{sample.id}</td>
                  <td>{sample.patient_name}</td>
                  <td>{sample.diagnosis}</td>
                  <td>{new Date(sample.date).toLocaleDateString()}</td>
                  <td>
                    <span className={`status-badge status-${sample.status.toLowerCase()}`}>
                      {sample.status}
                    </span>
                  </td>
                  <td>
                    <button
                      className="action-btn"
                      onClick={() => onPatientSelect(sample)}
                    >
                      View Details
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="no-data">
                  No samples found
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="info-cards">
        <div className="info-card">
          <h3>🩺 A2 Clinical Module</h3>
          <p>Patient records, medical files, and clinical data management</p>
        </div>
        <div className="info-card">
          <h3>🧬 A3 Genomic Module</h3>
          <p>DNA sequence analysis, primer design, variant detection, and NCBI integration</p>
        </div>
      </div>
    </div>
  );
}
