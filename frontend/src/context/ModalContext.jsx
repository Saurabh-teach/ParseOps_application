import React, { createContext, useState, useContext, useCallback } from 'react';
import { XCircle, CheckCircle, AlertTriangle, X } from 'lucide-react';

const ModalContext = createContext(null);

export const ModalProvider = ({ children }) => {
  const [modalState, setModalState] = useState({
    isOpen: false,
    type: 'info', // 'error', 'success', 'confirm'
    title: '',
    message: '',
    onConfirm: null,
  });

  const openModal = useCallback((type, title, message, onConfirm = null) => {
    setModalState({
      isOpen: true,
      type,
      title,
      message,
      onConfirm,
    });
  }, []);

  const closeModal = useCallback(() => {
    setModalState(prev => ({ ...prev, isOpen: false }));
  }, []);

  const handleConfirm = useCallback(() => {
    if (modalState.onConfirm) {
      modalState.onConfirm();
    }
    closeModal();
  }, [modalState.onConfirm, closeModal]);

  const showError = useCallback((message, title = 'Error') => {
    openModal('error', title, message);
  }, [openModal]);

  const showSuccess = useCallback((message, title = 'Success') => {
    openModal('success', title, message);
  }, [openModal]);

  const showConfirmation = useCallback((message, onConfirm, title = 'Confirm Action') => {
    openModal('confirm', title, message, onConfirm);
  }, [openModal]);

  const getIcon = () => {
    switch (modalState.type) {
      case 'error': return <XCircle className="global-modal-icon error" />;
      case 'success': return <CheckCircle className="global-modal-icon success" />;
      case 'confirm': return <AlertTriangle className="global-modal-icon confirm" />;
      default: return null;
    }
  };

  return (
    <ModalContext.Provider value={{ showError, showSuccess, showConfirmation }}>
      {children}
      {modalState.isOpen && (
        <div className="global-modal-overlay">
          <div className="global-modal-container">
            <div className={`global-modal-header ${modalState.type}`}>
              <div className="global-modal-title">
                {getIcon()}
                <span>{modalState.title}</span>
              </div>
              <button className="global-modal-close" onClick={closeModal}>
                <X size={18} />
              </button>
            </div>
            
            <div className="global-modal-body">
              <p>{modalState.message}</p>
            </div>
            
            <div className="global-modal-footer">
              {modalState.type === 'confirm' ? (
                <>
                  <button className="global-modal-btn cancel" onClick={closeModal}>Cancel</button>
                  <button className="global-modal-btn ok" onClick={handleConfirm}>OK</button>
                </>
              ) : (
                <button className="global-modal-btn ok" onClick={closeModal}>OK</button>
              )}
            </div>
          </div>
        </div>
      )}
    </ModalContext.Provider>
  );
};

export const useModal = () => {
  const context = useContext(ModalContext);
  if (!context) {
    throw new Error('useModal must be used within a ModalProvider');
  }
  return context;
};
