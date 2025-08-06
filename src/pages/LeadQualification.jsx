import React from 'react'
import { Button } from '../components/ui/button'
import { Link } from 'react-router-dom'

export default function LeadQualification() {
  return (
    <div className="container mx-auto px-4 py-8">
      <Link to="/">
        <Button variant="ghost" className="mb-4">← Back to Home</Button>
      </Link>
      <h1 className="text-4xl font-bold mb-6">Lead Qualification</h1>
      <p className="text-xl mb-4">
        Smart filtering and qualification process to help you focus on high-quality leads.
      </p>
      <div className="grid gap-4">
        <div className="bg-card p-6 rounded-lg shadow">
          <h2 className="text-2xl font-semibold mb-2">Qualification Process</h2>
          <ul className="list-disc pl-6 space-y-2">
            <li>Lead scoring based on multiple factors</li>
            <li>Behavior analysis</li>
            <li>Engagement tracking</li>
            <li>Priority ranking</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
