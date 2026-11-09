import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './styles/index.css'
import App from './App'
import { initScroll } from './lib/scroll'

// Smooth scrolling exists for the whole life of the page, so start it once here.
initScroll()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
