import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const Login = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { login, loading } = useAuth();
    const navigate = useNavigate();

    const handleSubmit = async (e) => {
        e.preventDefault();
        const success = await login(username, password);
        if (success) {
            navigate('/dashboard');
        } else {
            setError('Identifiants invalides');
        }
    };

    return (
        <div className="login-container">
            <div className="card">
                <h1>ZeroTrust Files</h1>
                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label>Nom d'utilisateur</label>
                        <input type="text" value={username} onChange={(e) => setUsername(e.target.value)} required />
                    </div>
                    <div className="form-group">
                        <label>Mot de passe</label>
                        <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
                    </div>
                    {error && <div className="error">{error}</div>}
                    <button type="submit" disabled={loading}>{loading ? 'Connexion...' : 'Se connecter'}</button>
                </form>
            </div>
        </div>
    );
};

export default Login;