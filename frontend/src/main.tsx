import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import { onCLS, onFCP, onLCP, onTTFB, type Metric } from 'web-vitals'
import App from './App'
import './index.css'

// Core Web Vitals monitoring
const reportWebVitals = (metric: Metric) => {
  // Only log in development to reduce production noise
  if (!import.meta.env.PROD) {
    console.log(`[Web Vitals] ${metric.name}: ${metric.value.toFixed(2)}ms (rating: ${metric.rating})`);
  }

  // Send to analytics service in production if needed
  // Example: analytics.track('web_vitals', { name: metric.name, value: metric.value });
};

// Initialize Web Vitals tracking
onCLS(reportWebVitals);
onFCP(reportWebVitals);
onLCP(reportWebVitals);
onTTFB(reportWebVitals);

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ConfigProvider
      locale={zhCN}
      theme={{
        token: {
          colorBgBase: '#0f172a',
          colorTextBase: '#f1f5f9',
          colorPrimary: '#00d9ff',
          fontFamily: "'Plus Jakarta Sans', 'Noto Sans SC', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        },
      }}
    >
      <App />
    </ConfigProvider>
  </React.StrictMode>,
)
