import { useState, useEffect } from 'react';
import { cn } from '../lib/utils';
import { getBaseUrl } from '@bagplus/shared/api';

const APP_VERSION = '1.0.0';
const PING_INTERVAL = 60000;

interface BackendStatus {
  online: boolean;
  version: string | null;
}

export default function StatusBar() {
  const [status, setStatus] = useState<BackendStatus>({ online: false, version: null });

  const ping = async () => {
    try {
      const res = await fetch(`${getBaseUrl()}/`, { signal: AbortSignal.timeout(5000) });
      if (res.ok) {
        const data = await res.json();
        setStatus({ online: true, version: data.version ?? null });
      } else {
        setStatus({ online: false, version: null });
      }
    } catch {
      setStatus({ online: false, version: null });
    }
  };

  useEffect(() => {
    ping();
    const interval = setInterval(ping, PING_INTERVAL);
    return () => clearInterval(interval);
  }, []);

  return (
    <footer className="h-8 bg-card border-t border-border px-4 flex items-center justify-between flex-shrink-0">
      <div className="flex items-center gap-3 text-sm text-muted-foreground">
        {status.version && (
          <span>API {status.version}</span>
        )}
        <span>App v{APP_VERSION}</span>
      </div>
      <div className="flex items-center gap-2">
        <span
          className={cn(
            'w-2 h-2 rounded-full flex-shrink-0',
            status.online ? 'bg-green-500' : 'bg-red-500'
          )}
        />
        <span className="text-sm text-muted-foreground">
          {status.online ? 'Online' : 'Offline'}
        </span>
      </div>
    </footer>
  );
}