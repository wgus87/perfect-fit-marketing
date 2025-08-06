import React from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent } from '../components/ui/card'

const About = () => {
  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8 }}
        className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8"
      >
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">About Us</h1>
          <p className="text-xl text-gray-600">
            Transforming Digital Marketing with AI Innovation
          </p>
        </div>

        <div className="space-y-8">
          <Card>
            <CardContent className="p-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Our Mission</h2>
              <p className="text-gray-600 mb-6">
                At Perfect Fit Digital Marketing Agency, we're on a mission to revolutionize digital marketing 
                through the power of artificial intelligence. We believe that every business deserves 
                marketing solutions that are as unique as they are effective.
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">What Sets Us Apart</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-blue-600 mb-2">AI-Powered Solutions</h3>
                  <p className="text-gray-600">
                    Our cutting-edge AI technology analyzes market trends and customer behavior 
                    to deliver actionable insights and optimize your marketing strategy.
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-blue-600 mb-2">Personalized Approach</h3>
                  <p className="text-gray-600">
                    We understand that every business is unique. Our solutions are tailored to 
                    your specific needs, goals, and target audience.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="p-6">
              <h2 className="text-2xl font-semibold text-gray-900 mb-4">Our Services</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="text-lg font-semibold text-blue-600 mb-2">Lead Generation</h3>
                  <p className="text-gray-600">
                    AI-powered lead generation that identifies and attracts your ideal prospects.
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-blue-600 mb-2">Lead Qualification</h3>
                  <p className="text-gray-600">
                    Smart filtering and scoring to focus your efforts on the most promising leads.
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-blue-600 mb-2">Sales Automation</h3>
                  <p className="text-gray-600">
                    Streamline your sales process with intelligent automation that feels personal.
                  </p>
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-blue-600 mb-2">Client Management</h3>
                  <p className="text-gray-600">
                    Build lasting relationships with comprehensive client management solutions.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </motion.div>
    </div>
  )
}

export default About
