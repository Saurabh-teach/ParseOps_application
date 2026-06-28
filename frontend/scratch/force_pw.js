  if (view === 'force_password_change') {
    return (
      <div className="auth-container">
        <div className="auth-left">
          <div className="auth-card">
            <div className="logo-container">
              <Lock size={32} color="#6366f1" />
            </div>
            <h1 className="form-title" style={{ fontSize: '1.5rem' }}>Change Your Password</h1>
            <p className="form-subtitle">For your security, please create a new password before continuing.</p>
            {error && <div className="error-message">{error}</div>}
            {message && <div className="success-message">{message}</div>}
            
            <form onSubmit={async (e) => {
              e.preventDefault();
              setLoading(true);
              setError('');
              try {
                await changePassword(formData.email, formData.password);
                setMessage('Password updated successfully!');
                await fetchWorkspaces(sessionStorage.getItem('access_token'));
              } catch (err) {
                setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to update password');
              } finally {
                setLoading(false);
              }
            }}>
              <div className="input-group">
                <label>Email Address</label>
                <div className="input-wrapper">
                  <input type="email" value={formData.email} disabled className="input-field" style={{ backgroundColor: '#f1f5f9' }} />
                </div>
              </div>
              <div className="input-group">
                <label>New Password</label>
                <div className="input-wrapper">
                  <input 
                    type={showPassword ? "text" : "password"} 
                    required
                    className="input-field"
                    value={formData.password}
                    onChange={e => setFormData({...formData, password: e.target.value})}
                  />
                  <button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)}>
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>
              <button type="submit" className="btn-primary" disabled={loading} style={{ marginTop: '1rem' }}>
                {loading ? <Loader2 className="animate-spin" /> : 'Update Password & Continue'}
              </button>
            </form>
          </div>
        </div>
        <div className="auth-right">
          <div className="auth-right-content">
            <h2 className="auth-quote">"Security is not a product, but a process."</h2>
            <p className="auth-author">- Bruce Schneier</p>
          </div>
        </div>
      </div>
    );
  }
