import { useState, useEffect } from 'react';
import Login from './components/Login';
import DoctorDashboard from './components/DoctorDashboard';
import PatientDashboard from './components/PatientDashboard';
import AdminDashboard from './components/AdminDashboard';
import HomePage from './components/HomePage';
import Navbar from './components/Navbar';
import RoleSelection from './components/RoleSelection';
import './App.css';

function App() {
  const [user, setUser] = useState(null);
  const [view, setView] = useState('home'); // home, role-selection, login
  const [selectedRole, setSelectedRole] = useState(null);

  useEffect(() => {
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      const userData = JSON.parse(storedUser);
      setUser(userData);
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
    setView('home');
  };

  const handleLogout = () => {
    localStorage.removeItem('user');
    setUser(null);
    setView('home');
  };

  const handleSelectRole = (role) => {
    setSelectedRole(role);
    setView('login');
  };

  if (user) {
    return (
      <div className="app">
        {user.role === 'doctor' && <DoctorDashboard onLogout={handleLogout} />}
        {(user.role === 'patient' || user.role === 'past_patient') && <PatientDashboard onLogout={handleLogout} />}
        {user.role === 'admin' && <AdminDashboard onLogout={handleLogout} />}
      </div>
    );
  }

  return (
    <div className="app">
      <Navbar
        onSignIn={() => setView('role-selection')}
        onHome={() => setView('home')}
      />

      <main style={{ paddingTop: '70px', backgroundColor: '#020202', background: '#020202' }}>
        {view === 'home' && (
          <HomePage onGetStarted={() => setView('role-selection')} />
        )}

        {view === 'role-selection' && (
          <RoleSelection onSelectRole={handleSelectRole} />
        )}

        {view === 'login' && (
          <Login
            onLogin={handleLogin}
            onBack={() => setView('role-selection')}
            initialRole={selectedRole}
          />
        )}
      </main>
    </div>
  );
}

export default App;
