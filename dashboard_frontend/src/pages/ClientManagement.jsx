import React from 'react'
import { Button } from '../components/ui/button'
import { Link } from 'react-router-dom'

export default function ClientManagement() {
  return (
    <div className="container mx-auto px-4 py-8">
      <Link to="/">
        <Button variant="ghost" className="mb-4">← Back to Home</Button>
      </Link>
      <h1 className="text-4xl font-bold mb-6">Client Management</h1>
      <p className="text-xl mb-4">
        Comprehensive client relationship management to ensure long-term success.
      </p>
      <div className="grid gap-4">
        <div className="bg-card p-6 rounded-lg shadow">
          <h2 className="text-2xl font-semibold mb-2">Management Tools</h2>
          <ul className="list-disc pl-6 space-y-2">
            <li>Client communication tracking</li>
            <li>Project milestone management</li>
            <li>Automated reporting</li>
            <li>Support ticket system</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
