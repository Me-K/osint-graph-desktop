import { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App.jsx';
import api from './desktopApi.js';
import './index.css';
import './setup.css';

// Choose between first-run administrator setup and the initialized desktop application.
function Desktop() {
  const [setup, setSetup] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    // Check whether the installation needs first-run account setup.
    api.get('/desktop/status').then(/* Choose the setup screen or application from the local installation status. */ ({ data }) => setSetup(data.setup_required))
      .catch(/* Display a failure to read the installation status. */ (err) => setError(err.message));
  }, []);

  // Validate the setup form, create the installation administrator, and sign in automatically.
  async function createAccount(event) {
    event.preventDefault();
    setError('');
    const values = Object.fromEntries(new FormData(event.currentTarget));
    if (values.password !== values.confirmation) {
      setError('Les deux mots de passe doivent être identiques.');
      return;
    }
    setBusy(true);
    try {
      await api.post('/desktop/setup', values);
      const { data } = await api.post('/auth/login', { user_id: values.user_id, password: values.password });
      window.sessionStorage.setItem('osint_graph_token', data.token);
      setSetup(false);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  if (setup === false) return <App />;
  return <main className="setup-page">
    <form className="setup-card" onSubmit={createAccount}>
      <div className="offline-badge">● APPLICATION LOCALE · HORS LIGNE</div>
      <h1>OSINT Graph</h1>
      {setup === null ? <p>{error || 'Ouverture de votre espace local…'}</p> : <>
        <p>Créez le compte administrateur de cet ordinateur. Vos graphes et vos comptes sont enregistrés sur ce poste.</p>
        <label>Identifiant<input name="user_id" autoFocus required minLength={3} maxLength={64} placeholder="admin" autoComplete="username" /></label>
        <label>Nom affiché<input name="display_name" placeholder="Administrateur" autoComplete="name" /></label>
        <label>Mot de passe<input name="password" required minLength={10} type="password" autoComplete="new-password" /></label>
        <small>Au moins 10 caractères, avec trois catégories parmi minuscules, majuscules, chiffres et symboles.</small>
        <label>Confirmer le mot de passe<input name="confirmation" required type="password" autoComplete="new-password" /></label>
        {error && <p role="alert" className="setup-error">{error}</p>}
        <button disabled={busy} type="submit">{busy ? 'Création…' : 'Créer mon espace local'}</button>
      </>}
    </form>
  </main>;
}

createRoot(document.getElementById('root')).render(<Desktop />);
