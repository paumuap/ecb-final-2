import { useState, useEffect } from 'react';
import './App.css';
import Dashboard from './pages/Dashboard';
import PatientDetails from './pages/PatientDetails';
import GenomicAnalysis from './pages/GenomicAnalysis';
import FileManagement from './pages/FileManagement';

const A2_API = 'http://127.0.0.1:8000/api';
const A3_API = 'http://127.0.0.1:8001/api';

type Page = 'dashboard' | 'patient' | 'genomics' | 'files' | 'analysis';

interface User {
  id: number;
  username: string;
  email: string;
  role: string;
}

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

function App() {
  const [user, setUser] = useState<User | null>(null);
  const [currentPage, setCurrentPage] = useState<Page>('dashboard');
  const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null);
  const [selectedGeneId, setSelectedGeneId] = useState<number | null>(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (token) {
      fetchUser(token);
    }
  }, []);

  const fetchUser = async (token: string) => {
    try {
      const response = await fetch(`${A2_API}/me`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
      } else {
        localStorage.removeItem('token');
      }
    } catch (err) {
      console.error('Failed to fetch user:', err);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch(`${A2_API}/login`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        fetchUser(data.access_token);
        setUsername('');
        setPassword('');
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Login failed');
      }
    } catch (err) {
      setError('An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    setUser(null);
    setCurrentPage('dashboard');
  };

  const handlePatientSelect = (patient: Patient) => {
    setSelectedPatient(patient);
    setCurrentPage('patient');
  };

  if (!user) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <div className="auth-header">
            <h1>🧬 GenLab</h1>
            <p>Integrated Clinical Genomics Platform</p>
          </div>
          
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label>Username</label>
              <input
                type="text"
                placeholder="Enter username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            <div className="form-group">
              <label>Password</label>
              <input
                type="password"
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={loading}
                required
              />
            </div>

            {error && <div className="error-msg">{error}</div>}

            <button type="submit" disabled={loading} className="login-btn">
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="auth-footer">
            <p><strong>Demo Credentials:</strong></p>
            <p>Username: <code>admin</code></p>
            <p>Password: <code>password</code></p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-content">
          <div className="logo-section">
            <h1>🧬 GenLab</h1>
            <p className="subtitle">Clinical Genomics Platform (A2 + A3)</p>
          </div>
          <div className="header-info">
            <span className="user-badge">
              👤 {user.username} 
              <span className="role">{user.role}</span>
            </span>
            <button className="logout-btn" onClick={handleLogout}>Sign Out</button>
          </div>
        </div>
      </header>

      <nav className="sidebar-nav">
        <div className="nav-section">
          <h3>Clinical Data (A2)</h3>
          <button
            className={`nav-item ${currentPage === 'dashboard' ? 'active' : ''}`}
            onClick={() => setCurrentPage('dashboard')}
          >
            <span className="icon">📊</span>
            <span className="label">Patients & Samples</span>
          </button>
          <button
            className={`nav-item ${currentPage === 'patient' ? 'active' : ''}`}
            onClick={() => selectedPatient && setCurrentPage('patient')}
            disabled={!selectedPatient}
          >
            <span className="icon">👨‍⚕️</span>
            <span className="label">Patient Details</span>
          </button>
          <button
            className={`nav-item ${currentPage === 'files' ? 'active' : ''}`}
            onClick={() => setCurrentPage('files')}
          >
            <span className="icon">📁</span>
            <span className="label">Medical Files</span>
          </button>
        </div>

        <div className="nav-section">
          <h3>Genomic Analysis (A3)</h3>
          <button
            className={`nav-item ${currentPage === 'genomics' ? 'active' : ''}`}
            onClick={() => setCurrentPage('genomics')}
          >
            <span className="icon">🧬</span>
            <span className="label">DNA Sequences</span>
          </button>
        </div>
      </nav>

      <main className="app-content">
        {currentPage === 'dashboard' && (
          <Dashboard 
            onPatientSelect={handlePatientSelect}
            apiUrl={A2_API}
            token={localStorage.getItem('token') || ''}
            user={user}
          />
        )}

        {currentPage === 'patient' && selectedPatient && (
          <PatientDetails
            patient={selectedPatient}
            apiUrlA2={A2_API}
            apiUrlA3={A3_API}
            token={localStorage.getItem('token') || ''}
          />
        )}

        {currentPage === 'genomics' && (
          <GenomicAnalysis
            apiUrl={A3_API}
            onGeneSelect={setSelectedGeneId}
          />
        )}

        {currentPage === 'analysis' && (
          <SequenceAnalysisPage
            apiUrl={A3_API}
          />
        )}

        {currentPage === 'files' && (
          <FileManagement
            apiUrl={A2_API}
            token={localStorage.getItem('token') || ''}
          />
        )}
      </main>

      <footer className="app-footer">
        <p>GenLab v1.0 • Integrating A2 (Clinical) + A3 (Genomic) • ECB Platform</p>
      </footer>
    </div>
  );
}
export default App;
