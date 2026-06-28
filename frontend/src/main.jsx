import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { ModalProvider } from './context/ModalContext.jsx'

import React from 'react'

class GlobalErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null, errorInfo: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    this.setState({ errorInfo })
    console.error("Global Error Caught:", error, errorInfo)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '2rem', margin: '2rem', border: '2px solid red', borderRadius: '8px', backgroundColor: '#fff5f5' }}>
          <h1 style={{ color: '#e53e3e', marginTop: 0 }}>Global Application Crash</h1>
          <p><strong>Error:</strong> {this.state.error?.toString()}</p>
          <pre style={{ backgroundColor: '#fcdbd9', padding: '1rem', borderRadius: '4px', overflowX: 'auto', fontSize: '0.8rem' }}>
            {this.state.error?.stack}
            {'\n\nComponent Stack:\n'}
            {this.state.errorInfo?.componentStack}
          </pre>
        </div>
      )
    }
    return this.props.children
  }
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <GlobalErrorBoundary>
      <ModalProvider>
        <App />
      </ModalProvider>
    </GlobalErrorBoundary>
  </StrictMode>,
)
