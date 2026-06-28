import re

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add state variable
if 'const [mustChangePassword, setMustChangePassword]' not in content:
    content = content.replace(
        "const [isLoggedIn, setIsLoggedIn] = useState(!!sessionStorage.getItem('access_token'));",
        "const [isLoggedIn, setIsLoggedIn] = useState(!!sessionStorage.getItem('access_token'));\n  const [mustChangePassword, setMustChangePassword] = useState(sessionStorage.getItem('mustChangePassword') === 'true');"
    )

# 2. Modify verifyLoginOTP logic
old_login_otp_logic = '''          if (data.requires_password_change) {
            setView('force_password_change');
            setFormData({ ...formData, password: '' });
          } else {
            await fetchWorkspaces(data.access);
          }'''
new_login_otp_logic = '''          if (data.requires_password_change) {
            sessionStorage.setItem('mustChangePassword', 'true');
            setMustChangePassword(true);
          }
          await fetchWorkspaces(data.access);'''
content = content.replace(old_login_otp_logic, new_login_otp_logic)

# 3. Add Modal to main layout
# We will inject the modal just before the `return` of the main `if (isLoggedIn)` block.
# Wait, let's just append it before `</WorkspaceLayout>` or at the end of the `isLoggedIn` return block.

modal_code = '''
      {mustChangePassword && (
        <div className="modal-overlay" style={{ zIndex: 9999 }}>
          <div className="modal-card">
            <div className="logo-container" style={{ textAlign: 'center', marginBottom: '1rem' }}>
              <Lock size={32} color="#6366f1" />
            </div>
            <h2 className="form-title" style={{ textAlign: 'center' }}>Change Your Password</h2>
            <p className="form-subtitle" style={{ textAlign: 'center', marginBottom: '2rem' }}>For your security, please create a new password before continuing.</p>
            {error && <div className="error-message">{error}</div>}
            {message && <div className="success-message">{message}</div>}
            
            <form onSubmit={async (e) => {
              e.preventDefault();
              setLoading(true);
              setError('');
              try {
                if (changePasswordData.new_password !== changePasswordData.confirm_password) {
                  setError("Passwords do not match");
                  setLoading(false);
                  return;
                }
                const email = sessionStorage.getItem('email');
                if (!email) throw new Error("Email not found in session");
                await changePassword(email, changePasswordData.new_password);
                setMessage('Password updated successfully!');
                sessionStorage.removeItem('mustChangePassword');
                setMustChangePassword(false);
                // Optionally reload workspaces or keep the user where they are
                await fetchWorkspaces(sessionStorage.getItem('access_token'));
              } catch (err) {
                setError(err.response?.data?.error || err.response?.data?.detail || 'Failed to update password');
              } finally {
                setLoading(false);
              }
            }}>
              <div className="input-group">
                <label>New Password</label>
                <div className="input-wrapper">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={changePasswordData.new_password}
                    onChange={e => setChangePasswordData({...changePasswordData, new_password: e.target.value})}
                    placeholder="Enter new password"
                    required
                  />
                  <button type="button" className="password-toggle" onClick={() => setShowPassword(!showPassword)}>
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>

              <div className="input-group">
                <label>Confirm Password</label>
                <div className="input-wrapper">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={changePasswordData.confirm_password}
                    onChange={e => setChangePasswordData({...changePasswordData, confirm_password: e.target.value})}
                    placeholder="Confirm new password"
                    required
                  />
                </div>
              </div>

              <button type="submit" className="submit-btn" disabled={loading}>
                {loading ? 'Updating...' : 'Update Password'}
              </button>
            </form>
          </div>
        </div>
      )}
'''

if '{mustChangePassword && (' not in content:
    content = content.replace(
        "{showAddGoalTask && (", 
        modal_code + "\n      {showAddGoalTask && ("
    )

with open('c:/Users/saura/ParseOps/frontend/src/App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
