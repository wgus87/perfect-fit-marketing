import React from 'react'
import { Button } from '../components/ui/button'
import { Link } from 'react-router-dom'

export default function SalesAutomation() {
  return (
    <div className="container mx-auto px-4 py-8">
      <Link to="/">
        <Button variant="ghost" className="mb-4">← Back to Home</Button>
      </Link>
      <h1 className="text-4xl font-bold mb-6">Sales Automation</h1>
      <p className="text-xl mb-4">
        Automated outreach that maintains a personal touch while maximizing efficiency.
      </p>
      <div className="grid gap-4">
        <div className="bg-card p-6 rounded-lg shadow">
          <h2 className="text-2xl font-semibold mb-2">Automation Features</h2>
          <ul className="list-disc pl-6 space-y-2">
            <li>Personalized email sequences</li>
            <li>Smart follow-up scheduling</li>
            <li>Response analysis</li>
            <li>Performance tracking</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
