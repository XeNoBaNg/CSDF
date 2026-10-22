import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { NewInvestigationPage } from './pages/NewInvestigationPage';
import { CaseHistoryPage } from './pages/CaseHistoryPage';
import { SystemStatusPage } from './pages/SystemStatusPage';
import { AudioInspectionPage } from './pages/AudioInspectionPage';
import { CrossComparisonPage } from './pages/CrossComparisonPage';
import { ErrorBoundary } from './components/common/ErrorBoundary';

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<DashboardPage />} />
            <Route path="cases" element={<CaseHistoryPage />} />
            <Route path="cases/new" element={<NewInvestigationPage />} />
            <Route path="compare" element={<CrossComparisonPage />} />
            <Route path="evidence/:evidenceId" element={<AudioInspectionPage />} />
            <Route path="status" element={<SystemStatusPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
};

export default App;
