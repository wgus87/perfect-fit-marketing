import "./App.css"
import { HashRouter as Router, Routes, Route } from 'react-router-dom'
import LandingPage from "./components/LandingPage"
import LeadGeneration from "./pages/LeadGeneration"
import LeadQualification from "./pages/LeadQualification"
import SalesAutomation from "./pages/SalesAutomation"
import ClientManagement from "./pages/ClientManagement"

function App() {
  return (
    <Router>
      <div className="App">
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/lead-generation" element={<LeadGeneration />} />
          <Route path="/lead-qualification" element={<LeadQualification />} />
          <Route path="/sales-automation" element={<SalesAutomation />} />
          <Route path="/client-management" element={<ClientManagement />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
