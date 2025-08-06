import "./App.css"
import { HashRouter as Router, Routes, Route } from 'react-router-dom'
import LandingPage from "./components/LandingPage"
import LeadGeneration from "./pages/LeadGeneration"
import LeadQualification from "./pages/LeadQualification"
import SalesAutomation from "./pages/SalesAutomation"
import ClientManagement from "./pages/ClientManagement"
import Contact from "./pages/Contact"
import About from "./pages/About"
import Chatbot from "./components/Chatbot"

function App() {
  return (
    <Router>
      <div className="App">
        <Chatbot />
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/lead-generation" element={<LeadGeneration />} />
          <Route path="/lead-qualification" element={<LeadQualification />} />
          <Route path="/sales-automation" element={<SalesAutomation />} />
          <Route path="/client-management" element={<ClientManagement />} />
          <Route path="/contact" element={<Contact />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </div>
    </Router>
  )
}

export default App
