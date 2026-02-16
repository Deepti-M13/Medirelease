import { useState } from 'react';
import { login, register } from '../utils/api';
import './Login.css';

export default function Login({ onLogin, onBack, initialRole }) {
    const [isLogin, setIsLogin] = useState(true);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState(initialRole || 'patient');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        try {
            let response;
            if (isLogin) {
                response = await login(username, password, role);
            } else {
                response = await register(username, password, role);
            }

            const userData = {
                userId: response.user_id,
                username: response.username,
                role: response.role,
            };
            localStorage.setItem('user', JSON.stringify(userData));
            onLogin(userData);
        } catch (err) {
            setError(err.response?.data?.detail || 'An error occurred');
        } finally {
            setLoading(false);
        }
    };

    const getRoleTitle = () => {
        switch (role) {
            case 'admin': return 'Admin Access';
            case 'doctor': return 'Doctor Portal';
            case 'patient': return 'Patient Care';
            default: return 'Healthcare Portal';
        }
    };

    return (
        <div className="login-container animate-fade-in">
            <div className="login-card card teal-glow animate-fade-up">
                <div className="login-header">
                    <button onClick={onBack} className="back-link hover-scale">
                        ← Choose different role
                    </button>
                    <h1 className="teal-gradient-text animate-slide-down">{getRoleTitle()}</h1>
                    <p className="login-subtitle">
                        {isLogin ? 'Welcome back! Please enter your details.' : 'Create an account to get started.'}
                    </p>
                </div>

                <div className="login-tabs">
                    <button
                        className={`tab-btn hover-glow ${isLogin ? 'active' : ''}`}
                        onClick={() => setIsLogin(true)}
                    >
                        Sign In
                    </button>
                    <button
                        className={`tab-btn hover-glow ${!isLogin ? 'active' : ''}`}
                        onClick={() => setIsLogin(false)}
                    >
                        Register
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="login-form">
                    <div className="form-group">
                        <label>Username</label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            required
                            placeholder="Enter your username"
                            className="hover-glow"
                        />
                    </div>

                    <div className="form-group">
                        <label>Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            required
                            placeholder="••••••••"
                            className="hover-glow"
                        />
                    </div>

                    {!initialRole && (
                        <div className="form-group">
                            <label>Role</label>
                            <select value={role} onChange={(e) => setRole(e.target.value)} className="hover-glow">
                                <option value="patient">Patient</option>
                                <option value="doctor">Doctor</option>
                                <option value="admin">Admin</option>
                            </select>
                        </div>
                    )}

                    {error && <div className="error-message animate-fade-in">{error}</div>}

                    <button type="submit" className="btn-primary btn-primary-shimmer btn-submit hover-scale" disabled={loading}>
                        {loading ? 'Processing...' : (isLogin ? 'Sign In' : 'Register')}
                    </button>
                </form>

                <div className="login-footer">
                    <p className="demo-hint">Demo: <code>{role}1 / password123</code></p>
                    <p className="security-note animate-pulse-slow">🔒 Enterprise-grade security enabled</p>
                </div>
            </div>
        </div>
    );
}
