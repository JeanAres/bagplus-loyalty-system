import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Home from './pages/Home';
import AtivarSacola from './pages/AtivarSacola';
import RegistrarUso from './pages/RegistrarUso';
import Devolucao from './pages/Devolucao';
import CadastrarCliente from './pages/CadastrarCliente';
import BuscarCliente from './pages/BuscarCliente';
import VerificarQr from './pages/VerificarQr';
import Historico from './pages/Historico';

export default function App() {
  return (
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <Layout>
                    <Routes>
                      <Route path="/" element={<Home />} />
                      <Route path="/ativar" element={<AtivarSacola />} />
                      <Route path="/registrar-uso" element={<RegistrarUso />} />
                      <Route path="/devolucao" element={<Devolucao />} />
                      <Route path="/cadastrar-cliente" element={<CadastrarCliente />} />
                      <Route path="/buscar-cliente" element={<BuscarCliente />} />
                      <Route path="/verificar-qr" element={<VerificarQr />} />
                      <Route path="/historico" element={<Historico />} />
                      <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                  </Layout>
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
}