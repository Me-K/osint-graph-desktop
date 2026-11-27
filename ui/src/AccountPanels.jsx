import { useCallback, useEffect, useState } from 'react';

const passwordHint = 'Au moins 10 caractères, avec trois catégories parmi minuscules, majuscules, chiffres et symboles.';
const roles = [['viewer', 'Lecture'], ['editor', 'Modification'], ['admin', 'Administration du graphe']];

// Render accessible error and success messages for account operations.
function Notice({ error, message }) {
  return <>{error && <p className="home-error" role="alert">{error}</p>}
    {message && <p className="home-success" role="status">{message}</p>}</>;
}

// Share busy, success, and error state across asynchronous account and permission forms.
function useAction(onAuthError) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  // Run a form operation with progress feedback and route authentication failures to the session handler.
  const run = async (operation) => {
    setBusy(true); setError(''); setMessage('');
    try { await operation(setMessage); }
    catch (err) { if (!onAuthError(err)) setError(err.message); }
    finally { setBusy(false); }
  };
  return { busy, run, notice: <Notice error={error} message={message} /> };
}

// Render the signed-in account's profile and password settings outside the graph editor.
export function MyAccount({ client, user, onUserChanged, onAuthError }) {
  const profile = useAction(onAuthError);
  const password = useAction(onAuthError);
  const [displayName, setDisplayName] = useState(user.display_name || '');
  return <section aria-labelledby="my-account-title">
    <h2 id="my-account-title">Mon compte</h2>
    <p className="home-muted">Gérez vos informations et votre mot de passe sur cet ordinateur.</p>
    <div className="home-columns">
      <form className="home-card home-form" data-testid="profile-form" onSubmit={(event) => {
        // Handle profile-form submission through the shared action state.
        event.preventDefault();
        profile.run(async (done) => {
          // Save the display name, refresh the signed-in profile, and show confirmation.
          const { data } = await client.put('/account/profile', { display_name: displayName });
          onUserChanged(data); done('Votre profil a été mis à jour.');
        });
      }}>
        <h3>Informations du compte</h3>
        <label>Identifiant<input value={user.id} readOnly /></label>
        <small className="home-muted">L’identifiant de connexion reste fixe.</small>
        <label>Nom affiché<input name="display_name" maxLength={120} value={displayName} onChange={/* Update the display name being edited in the profile form. */ (e) => setDisplayName(e.target.value)} autoComplete="name" /></label>
        <p>Rôle : <strong>{user.is_admin ? 'Administrateur des comptes' : 'Utilisateur'}</strong></p>
        {profile.notice}
        <button disabled={profile.busy} className="home-primary">Enregistrer mon profil</button>
      </form>
      <form className="home-card home-form" data-testid="password-form" onSubmit={(event) => {
        // Read the password form and start the authenticated password-change operation.
        event.preventDefault();
        const form = event.currentTarget;
        const values = Object.fromEntries(new FormData(form));
        password.run(async (done) => {
          // Check password confirmation, request the change, and clear the password fields on success.
          if (values.new_password !== values.confirmation) throw new Error('Les deux nouveaux mots de passe doivent être identiques.');
          await client.post('/account/password', { current_password: values.current_password, new_password: values.new_password });
          form.reset(); done('Mot de passe modifié. Les autres sessions ont été déconnectées.');
        });
      }}>
        <h3>Changer mon mot de passe</h3>
        <label>Mot de passe actuel<input name="current_password" type="password" required autoComplete="current-password" /></label>
        <label>Nouveau mot de passe<input name="new_password" type="password" required minLength={10} maxLength={1024} autoComplete="new-password" /></label>
        <small className="home-muted">{passwordHint}</small>
        <label>Confirmer le nouveau mot de passe<input name="confirmation" type="password" required autoComplete="new-password" /></label>
        {password.notice}
        <button disabled={password.busy} className="home-primary">Changer mon mot de passe</button>
      </form>
    </div>
  </section>;
}

// Render administrator controls for an account's profile, role, status, lock, and password.
function AccountEditor({ account, client, currentUser, onSaved, onAuthError }) {
  const action = useAction(onAuthError);
  const reset = useAction(onAuthError);
  const [name, setName] = useState(account.display_name || '');
  const [admin, setAdmin] = useState(account.is_admin);
  const [disabled, setDisabled] = useState(account.disabled);
  const ownAccount = account.id === currentUser.id;
  return <div className="home-card">
    <form className="home-form" data-testid="account-edit-form" onSubmit={(event) => {
      // Confirm account deactivation when needed and submit the account edits.
      event.preventDefault();
      if (disabled && !account.disabled && !window.confirm(`Désactiver le compte « ${account.id} » et fermer ses sessions ?`)) return;
      action.run(async (done) => {
        // Save the account profile, application role, and enabled status, then refresh its list entry.
        const { data } = await client.put(`/admin/accounts/${encodeURIComponent(account.id)}`, { display_name: name, is_admin: admin, disabled });
        onSaved(data); done('Compte mis à jour.');
      });
    }}>
      <h3>Compte : {account.id}</h3>
      <label>Nom affiché<input name="display_name" value={name} maxLength={120} onChange={/* Update the display name in the administrator's account editor. */ (e) => setName(e.target.value)} /></label>
      <label>Rôle dans l’application<select name="is_admin" value={String(admin)} onChange={/* Convert the selected application role to its administrator flag. */ (e) => setAdmin(e.target.value === 'true')}>
        <option value="false">Utilisateur</option><option value="true">Administrateur des comptes</option>
      </select></label>
      <label>État du compte<select name="disabled" value={String(disabled)} disabled={ownAccount} onChange={/* Convert the selected account state to its disabled flag. */ (e) => setDisabled(e.target.value === 'true')}>
        <option value="false">Actif</option><option value="true">Désactivé</option>
      </select></label>
      <small className="home-muted">La désactivation conserve les graphes et les droits, et empêche toute connexion.</small>
      {action.notice}
      <button className="home-primary" disabled={action.busy}>Enregistrer ce compte</button>
      {account.locked && <button type="button" disabled={action.busy} onClick={/* Start an account-unlock operation with shared progress and error handling. */ () => action.run(async (done) => {
        // Clear the account's login lock and refresh its displayed status.
        const { data } = await client.post(`/admin/accounts/${encodeURIComponent(account.id)}/unlock`, {});
        onSaved(data); done('Compte débloqué.');
      })}>Débloquer ce compte</button>}
    </form>
    {!ownAccount && <form className="home-form account-reset" data-testid="account-reset-form" onSubmit={(event) => {
      // Read the administrator's password-reset form and start the reset operation.
      event.preventDefault();
      const form = event.currentTarget;
      const values = Object.fromEntries(new FormData(form));
      reset.run(async (done) => {
        // Validate password confirmation, reset the account password, and clear the form on success.
        if (values.new_password !== values.confirmation) throw new Error('Les deux mots de passe doivent être identiques.');
        await client.post(`/admin/accounts/${encodeURIComponent(account.id)}/password`, { new_password: values.new_password });
        form.reset(); onSaved({ ...account, locked: false });
        done('Mot de passe réinitialisé. Les sessions de ce compte ont été fermées.');
      });
    }}>
      <h3>Réinitialiser le mot de passe</h3>
      <label>Nouveau mot de passe<input type="password" name="new_password" required minLength={10} maxLength={1024} autoComplete="new-password" /></label>
      <small className="home-muted">{passwordHint}</small>
      <label>Confirmer le mot de passe<input type="password" name="confirmation" required autoComplete="new-password" /></label>
      {reset.notice}<button disabled={reset.busy}>Réinitialiser le mot de passe</button>
    </form>}
    {ownAccount && <p className="home-muted">Pour votre mot de passe, utilisez « Mon compte ».</p>}
  </div>;
}

// Load and filter local accounts and present separate account creation and editing forms.
export function AccountManagement({ client, user, onUserChanged, onAuthError }) {
  const [accounts, setAccounts] = useState([]);
  const [selectedId, setSelectedId] = useState('');
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const creation = useAction(onAuthError);
  const [query, setQuery] = useState('');
  useEffect(() => {
    // Load local accounts and ignore asynchronous results after the panel is released.
    let active = true;
    client.get('/admin/accounts').then(/* Store loaded account details while the account panel is still active. */ ({ data }) => { if (active) setAccounts(data); })
      .catch(/* Handle session errors or display the account-list loading failure while the panel is active. */ (err) => { if (active && !onAuthError(err)) setLoadError(err.message); })
      .finally(/* Clear the account-list loading indicator after the request finishes. */ () => { if (active) setLoading(false); });
    return /* Prevent a completed request from updating an inactive account panel. */ () => { active = false; };
  }, [client, onAuthError]);
  const selected = accounts.find(/* Find the account currently selected for editing. */ (account) => account.id === selectedId);
  // Replace an edited account in the list and refresh session details when it is the current account.
  function saved(account) {
    setAccounts(/* Build the next account list from its latest state and the saved account details. */ (previous) => previous.map(/* Replace only the account whose identifier matches the saved record. */ (item) => item.id === account.id ? account : item));
    if (account.id === user.id) onUserChanged(account);
  }
  return <section aria-labelledby="accounts-title">
    <h2 id="accounts-title">Gestion des comptes</h2>
    <p className="home-muted">Créez et administrez les comptes de cette installation. Les accès aux graphes se règlent séparément.</p>
    <Notice error={loadError} />
    <div className="home-columns">
      <div className="home-card">
        <div className="home-section-heading"><h3>Comptes locaux</h3><button type="button" onClick={/* Clear account selection to show the account creation form. */ () => setSelectedId('')}>Nouveau compte</button></div>
        <label className="home-search">Rechercher un compte<input value={query} onChange={/* Update the account-search query. */ (e) => setQuery(e.target.value)} placeholder="Identifiant ou nom" /></label>
        {loading ? <p>Chargement des comptes…</p> : <div className="account-list">
          {accounts.filter(/* Match account identifiers and display names against the case-insensitive search query. */ (account) => `${account.id} ${account.display_name || ''}`.toLowerCase().includes(query.toLowerCase())).map(/* Render a selectable account row with its application role and status. */ (account) =>
            <button type="button" key={account.id} data-account-id={account.id} className={`account-row ${selectedId === account.id ? 'selected' : ''}`} onClick={/* Select this account for administration. */ () => setSelectedId(account.id)}>
              <span><strong>{account.display_name || account.id}</strong><small>{account.id}</small></span>
              <span className="account-badges"><span>{account.is_admin ? 'Administrateur' : 'Utilisateur'}</span>
                <span>{account.disabled ? 'Désactivé' : account.locked ? 'Verrouillé' : 'Actif'}</span></span>
            </button>)}
        </div>}
      </div>
      {selected ? <AccountEditor key={selected.id} account={selected} client={client} currentUser={user} onSaved={saved} onAuthError={onAuthError} /> :
        <form className="home-card home-form" data-testid="account-create-form" onSubmit={(event) => {
          // Read the new-account form and start account creation.
          event.preventDefault();
          const form = event.currentTarget;
          const values = Object.fromEntries(new FormData(form));
          creation.run(async (done) => {
            // Validate confirmation, create the account, refresh the sorted list, and reset the form.
            if (values.password !== values.confirmation) throw new Error('Les deux mots de passe doivent être identiques.');
            const { data } = await client.post('/admin/accounts', { user_id: values.user_id, display_name: values.display_name, password: values.password, is_admin: values.is_admin === 'true' });
            setAccounts(/* Append the newly created account to the latest list and restore identifier ordering. */ (previous) => [...previous, data].sort(/* Sort accounts alphabetically by login identifier. */ (a, b) => a.id.localeCompare(b.id)));
            form.reset(); done(`Compte « ${data.id} » créé. Vous pouvez maintenant lui attribuer des accès aux graphes.`);
          });
        }}>
          <h3>Créer un compte</h3>
          <label>Identifiant<input name="user_id" required minLength={3} maxLength={64} autoComplete="off" /></label>
          <label>Nom affiché<input name="display_name" maxLength={120} /></label>
          <label>Rôle dans l’application<select name="is_admin" defaultValue="false"><option value="false">Utilisateur</option><option value="true">Administrateur des comptes</option></select></label>
          <label>Mot de passe initial<input name="password" type="password" required minLength={10} maxLength={1024} autoComplete="new-password" /></label>
          <small className="home-muted">{passwordHint}</small>
          <label>Confirmer le mot de passe<input name="confirmation" type="password" required autoComplete="new-password" /></label>
          {creation.notice}<button className="home-primary" disabled={creation.busy}>Créer le compte</button>
        </form>}
    </div>
  </section>;
}

// Render permission assignment, role editing, and access removal for one administered graph.
function GraphAccessEditor({ graph, client, onAuthError, onGraphsChanged }) {
  const [permissions, setPermissions] = useState([]);
  const [loadError, setLoadError] = useState('');
  const action = useAction(onAuthError);
  const path = `/graphs/${encodeURIComponent(graph.id)}/permissions`;
  // Reload the selected graph's permission assignments after a successful change.
  const load = useCallback(async () => {
    const { data } = await client.get(path); setPermissions(data);
  }, [client, path]);
  useEffect(() => {
    // Load the selected graph's permissions while guarding against responses to an inactive panel.
    let active = true;
    client.get(path).then(/* Store loaded graph permissions while their panel is active. */ ({ data }) => { if (active) setPermissions(data); })
      .catch(/* Handle authentication errors or show a graph-permission loading failure. */ (err) => { if (active && !onAuthError(err)) setLoadError(err.message); });
    return /* Ignore permission-loading results after the panel is released. */ () => { active = false; };
  }, [client, path, onAuthError]);
  // Apply a permission change, refresh graph access, and reload permissions only if administration is retained.
  const update = async (operation, done) => {
    await operation();
    const graphs = await onGraphsChanged();
    if (graphs.some(/* Check that the current account still administers this graph after the permission change. */ (item) => item.id === graph.id && item.role === 'admin')) await load();
    done('Accès mis à jour.');
  };
  return <div className="home-card">
    <h3>Accès à « {graph.name} »</h3>
    <Notice error={loadError} />{action.notice}
    <form className="home-inline-form" data-testid="graph-access-form" onSubmit={(event) => {
      // Read an existing account identifier and role from the graph-access form.
      event.preventDefault();
      const form = event.currentTarget;
      const values = Object.fromEntries(new FormData(form));
      action.run(/* Grant access, refresh permission state, and reset the form after success. */ async (done) => { await update(/* Submit the requested graph role for an existing account. */ () => client.post(path, values), done); form.reset(); });
    }}>
      <label>Identifiant d’un compte existant<input name="user_id" required placeholder="Identifiant du compte" /></label>
      <label>Droit sur ce graphe<select name="role" defaultValue="viewer">{roles.map(/* Render a graph-role option with its user-facing label. */ ([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <button className="home-primary" disabled={action.busy}>Attribuer un accès</button>
    </form>
    <div className="access-list">{permissions.map(/* Render an account's graph role and access-removal controls. */ (permission) => <div key={permission.user_id} className="access-row">
      <div><strong>{permission.display_name || permission.user_id}</strong><small>{permission.user_id}{permission.disabled ? ' · Compte désactivé' : ''}</small></div>
      <select aria-label={`Droit de ${permission.user_id}`} disabled={action.busy || permission.disabled} value={permission.role} onChange={(e) => {
        // Read the newly selected graph role and start its update.
        const role = e.target.value;
        action.run(/* Apply a graph-role change through the permission-refresh workflow. */ (done) => update(/* Send the new graph role for this account to the API. */ () => client.put(`${path}/${encodeURIComponent(permission.user_id)}`, { role }), done));
      }}>{roles.map(/* Render a graph-role option with its user-facing label. */ ([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
      <button disabled={action.busy} className="home-danger" onClick={() => {
        // Confirm removal before revoking this account's graph access.
        if (window.confirm(`Retirer l’accès de « ${permission.user_id} » à ce graphe ?`))
          action.run(/* Remove graph access through the permission-refresh workflow. */ (done) => update(/* Request deletion of this account's permission on the graph. */ () => client.delete(`${path}/${encodeURIComponent(permission.user_id)}`), done));
      }}>Retirer l’accès</button>
    </div>)}</div>
  </div>;
}

// Choose an administered graph and display its access controls on the home page.
export function GraphAccess({ graphs, client, onAuthError, onGraphsChanged }) {
  const manageable = graphs.filter(/* Keep only graphs administered by the current account. */ (graph) => graph.role === 'admin');
  const [selectedId, setSelectedId] = useState('');
  const selected = manageable.find(/* Find the graph currently selected for permission management. */ (graph) => graph.id === selectedId) || manageable[0];
  return <section>
    <h2>Accès aux graphes</h2>
    <p className="home-muted">Attribuez des droits aux comptes existants, sans ouvrir le studio.</p>
    {selected ? <>
      <label className="home-graph-select">Graphe à administrer<select value={selected.id} onChange={/* Select the graph whose permissions should be displayed. */ (e) => setSelectedId(e.target.value)}>
        {manageable.map(/* Render an administered graph in the permission-management selector. */ (graph) => <option key={graph.id} value={graph.id}>{graph.name}</option>)}
      </select></label>
      <GraphAccessEditor key={selected.id} graph={selected} client={client} onAuthError={onAuthError} onGraphsChanged={onGraphsChanged} />
    </> : <p>Vous n’administrez aucun graphe.</p>}
  </section>;
}
