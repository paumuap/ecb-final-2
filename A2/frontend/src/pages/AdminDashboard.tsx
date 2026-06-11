import { User } from '../api';
import '../styles/Dashboard.css';

interface AdminDashboardProps {
  user: User;
  onLogout: () => void;
}

export function AdminDashboard({ user, onLogout }: AdminDashboardProps) {
  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>Admin Dashboard</h1>
        <div className="header-actions">
          <span>Welcome, {user.username}</span>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>
      </header>

      <div className="dashboard-content">
        <h2>Admin view - All patients visible</h2>
        <p>Welcome {user.username}! This is the admin dashboard.</p>
      </div>
    </div>
  );
}
