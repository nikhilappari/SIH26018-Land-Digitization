import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Navbar from './components/Navbar';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Upload from './pages/Upload';
import ProcessingResults from './pages/ProcessingResults';
import VerificationQueue from './pages/VerificationQueue';
import VerificationWorkspace from './pages/VerificationWorkspace';
import Search from './pages/Search';
import RecordDetails from './pages/RecordDetails';
import MapVisualization from './pages/MapVisualization';
import { authService } from './services/api';

// Route guard for protected dashboard pages
const ProtectedRoute = ({ children }) => {
  if (!authService.isAuthenticated()) {
    authService.logout();
    return <Navigate to="/login" replace />;
  }

  return children;
};

// Main Layout wrapping full-width navbar and sidebar below it
const MainLayout = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50">
      <Navbar />
      <div className="flex flex-1">
        <Sidebar />
        <main className="p-8 flex-1 overflow-y-auto min-h-[calc(100vh-4rem)]">
          {children}
        </main>
      </div>
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Authentication Route */}
        <Route path="/login" element={<Login />} />

        {/* Protected Dashboard Routes */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Dashboard />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/upload"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Upload />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/processing/:id"
          element={
            <ProtectedRoute>
              <MainLayout>
                <ProcessingResults />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/verification"
          element={
            <ProtectedRoute>
              <MainLayout>
                <VerificationQueue />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/queue"
          element={
            <ProtectedRoute>
              <Navigate to="/verification" replace />
            </ProtectedRoute>
          }
        />
        <Route
          path="/verify/:id"
          element={
            <ProtectedRoute>
              <MainLayout>
                <VerificationWorkspace />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/search"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Search />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/details/:id"
          element={
            <ProtectedRoute>
              <MainLayout>
                <RecordDetails />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/records/:id"
          element={
            <ProtectedRoute>
              <MainLayout>
                <RecordDetails />
              </MainLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/map"
          element={
            <ProtectedRoute>
              <MainLayout>
                <MapVisualization />
              </MainLayout>
            </ProtectedRoute>
          }
        />

        {/* Fallback Catch-all Route */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
