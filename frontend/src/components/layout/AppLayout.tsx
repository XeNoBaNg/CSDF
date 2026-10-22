import React, { useEffect, useState, useCallback } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { fetchHealthStatus } from '../../api/health';
import type { HealthCheckResponse } from '../../types';

export const AppLayout: React.FC = () => {
  const [healthData, setHealthData] = useState<HealthCheckResponse | null>(null);
  const [apiStatus, setApiStatus] = useState<'healthy' | 'degraded' | 'offline' | 'checking'>('checking');
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const checkHealth = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchHealthStatus();
      setHealthData(data);
      setApiStatus(data.status === 'healthy' ? 'healthy' : 'degraded');
    } catch (error) {
      console.warn('Backend API connection check failed:', error);
      setApiStatus('offline');
      setHealthData(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    checkHealth();
    // Re-check periodically every 30 seconds
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, [checkHealth]);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-slate-950 text-slate-100 font-sans">
      {/* Sidebar Navigation */}
      <Sidebar apiStatus={apiStatus} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Header
          healthData={healthData}
          isLoading={isLoading}
          onRefresh={checkHealth}
        />

        <main className="flex-1 overflow-y-auto p-6 lg:p-8 bg-slate-950">
          <Outlet context={{ healthData, apiStatus, refreshHealth: checkHealth }} />
        </main>
      </div>
    </div>
  );
};
