import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './index.css'

// Add Inter font
const link = document.createElement('link')
link.rel = 'stylesheet'
link.href = 'https://rsms.me/inter/inter.css'
document.head.appendChild(link)

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
