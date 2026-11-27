import { useMemo, useRef, useState } from 'react';
import api from './desktopApi.js';
import { AccountManagement, MyAccount, GraphAccess } from './AccountPanels.jsx';
import './home.css';

const roleNames = { viewer: 'Lecture', editor: 'Modification', admin: 'Administration' };

// Render the graph library and separate account, account-administration, and graph-access sections.
export default function Home({ token, user, graphs, onOpenGraph, onCreateGraph, onImportGraph,
  creatingGraph, importingGraph, graphError, graphMessage, authError,
  onLogout, onUserChanged, onAuthError, onGraphsChanged }) {
  const [tab, setTab] = useState('graphs');
  const importRef = useRef(null);
  // Create an API adapter that attaches the current session token to every home-page request.
  const client = useMemo(() => {
    const config = { headers: { Authorization: `Bearer ${token}` } };
    return {
      get: /* Read a local API resource using the current session token. */ (path) => api.get(path, config),
      post: /* Submit local API data using the current session token. */ (path, data) => api.post(path, data, config),
      put: /* Update a local API resource using the current session token. */ (path, data) => api.put(path, data, config),
      delete: /* Delete a local API resource using the current session token. */ (path) => api.delete(path, config),
    };
  }, [token]);
  const canManageAccess = graphs.some(/* Check whether any graph grants access to the graph-permission management section. */ (graph) => graph.role === 'admin');
  const activeTab = tab === 'accounts' && !user.is_admin ? 'account' : tab;
  const items = [ ['graphs', 'Mes graphes'], ['account', 'Mon compte'],
    ...(user.is_admin ? [['accounts', 'Gestion des comptes']] : []),
    ...(canManageAccess ? [['access', 'Accès aux graphes']] : []) ];
  return <main className="home-page">
    <div className="home-container">
      <header className="home-header">
        <div><span className="home-offline">● ESPACE LOCAL · HORS LIGNE</span><h1>OSINT Graph</h1>
          <p className="home-muted">Vos graphes et votre compte, au même endroit.</p></div>
        <div className="home-session"><strong>{user.display_name || user.id}</strong>
          <span>{user.id} · {user.is_admin ? 'Administrateur des comptes' : 'Utilisateur'}</span>
          <button type="button" onClick={onLogout}>Se déconnecter</button></div>
      </header>
      <nav className="home-tabs" aria-label="Navigation de l’accueil">
        {items.map(/* Render a home-navigation tab with its active-page indicator. */ ([id, label]) => <button key={id} type="button" aria-current={activeTab === id ? 'page' : undefined}
          onClick={/* Switch to the chosen home-page section. */ () => setTab(id)}>{label}</button>)}
      </nav>
      {authError && <p role="alert" className="home-error">{authError}</p>}
      {activeTab === 'graphs' && <section aria-labelledby="graphs-title">
        <div className="home-section-heading"><div><h2 id="graphs-title">Mes graphes</h2><p className="home-muted">Choisissez un graphe pour ouvrir le studio.</p></div>
          <div className="home-actions">
            <button type="button" className="home-primary" onClick={onCreateGraph} disabled={creatingGraph || importingGraph}>
              {creatingGraph ? 'Création…' : 'Créer un nouveau graphe'}</button>
            <button type="button" onClick={/* Open the JSON file picker for a graph-library import. */ () => importRef.current?.click()} disabled={creatingGraph || importingGraph}>
              {importingGraph ? 'Import en cours…' : 'Importer un graphe'}</button>
            <input ref={importRef} hidden type="file" accept="application/json,.json" onChange={onImportGraph} />
          </div></div>
        {graphError && <p role="alert" className="home-error">{graphError}</p>}
        {graphMessage && <p role="status" className="home-success">{graphMessage}</p>}
        {graphs.length ? <div className="home-graphs">{graphs.map(/* Render a graph library card showing its metadata and the account's role. */ (graph) =>
          <button type="button" key={graph.id} className="home-graph-card" onClick={/* Open this graph in the studio. */ () => onOpenGraph(graph.id)}>
            <div className="home-section-heading"><h3>{graph.name}</h3><span className="home-role">{roleNames[graph.role]}</span></div>
            <p>{graph.description || 'Sans description'}</p><small>Créé par {graph.created_by}</small>
            <strong className="home-open">Ouvrir le graphe →</strong>
          </button>)}</div> : <div className="home-empty">Aucun graphe disponible pour ce compte. Créez ou importez votre premier graphe.</div>}
      </section>}
      {activeTab === 'account' && <MyAccount client={client} user={user} onUserChanged={onUserChanged} onAuthError={onAuthError} />}
      {activeTab === 'accounts' && user.is_admin && <AccountManagement client={client} user={user} onUserChanged={onUserChanged} onAuthError={onAuthError} />}
      {activeTab === 'access' && <GraphAccess graphs={graphs} client={client} onAuthError={onAuthError} onGraphsChanged={onGraphsChanged} />}
    </div>
  </main>;
}
