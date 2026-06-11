import { User } from '../api';
import '../styles/Dashboard.css';

interface UserDashboardProps {
  user: User;
  onLogout: () => void;
}

export function UserDashboard({ user, onLogout }: UserDashboardProps) {
  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>User Dashboard</h1>
        <div className="header-actions">
          <span>Welcome, {user.username}</span>
          <button onClick={onLogout} className="logout-btn">Logout</button>
        </div>
      </header>

      <div className="dashboard-content">
        <h2>User view - Your patients only</h2>
        <p>Welcome {user.username}! This is your personal dashboard.</p>
      </div>
    </div>
  );
}
