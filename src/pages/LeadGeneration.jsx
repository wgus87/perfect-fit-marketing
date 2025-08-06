import React from 'react'
import { Button } from '../components/ui/button'
import { Link } from 'react-router-dom'

export default function LeadGeneration() {
  return (
    <div className="container mx-auto px-4 py-8">
      <Link to="/">
        <Button variant="ghost" className="mb-4">← Back to Home</Button>
      </Link>
      <h1 className="text-4xl font-bold mb-6">Lead Generation</h1>
      <p className="text-xl mb-4">
        Our AI-powered lead generation service helps you find the perfect prospects for your business.
      </p>
      <div className="grid gap-4">
        <div className="bg-card p-6 rounded-lg shadow">
          <h2 className="text-2xl font-semibold mb-2">How it Works</h2>
          <ul className="list-disc pl-6 space-y-2">
            <li>AI analyzes your ideal customer profile</li>
            <li>Searches multiple data sources</li>
            <li>Identifies high-potential leads</li>
            <li>Validates contact information</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
