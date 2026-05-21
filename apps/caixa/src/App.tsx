import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AtivarSacola from './pages/AtivarSacola';
import RegistrarUso from './pages/RegistrarUso';
import Devolucao from './pages/Devolucao';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/ativar"
            element={
              <ProtectedRoute>
                <AtivarSacola />
              </ProtectedRoute>
            }
          />
          <Route
            path="/registrar-uso"
            element={
              <ProtectedRoute>
                <RegistrarUso />
              </ProtectedRoute>
            }
          />
          <Route
            path="/devolucao"
            element={
              <ProtectedRoute>
                <Devolucao />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}