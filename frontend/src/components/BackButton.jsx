const BackButton = ({ label = '← Back' }) => {
  const handleClick = () => {
    // Use browser history to go back if possible
    if (window.history.length > 1) {
      window.history.back();
    } else {
      // Fallback: navigate to home page
      window.location.href = '/';
    }
  };

  return (
    <button
      onClick={handleClick}
      style={{
        background: 'transparent',
        border: 'none',
        color: '#6366f1',
        fontSize: '0.9rem',
        cursor: 'pointer',
        marginBottom: '1rem',
        padding: 0,
      }}
    >
      {label}
    </button>
  );
};

export default BackButton;
