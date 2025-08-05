import React, { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { Button } from './ui/button'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './ui/card'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { Form } from './ui/form'
import { useIsMobile } from '../hooks/use-mobile'

const LandingPage = () => {
  const isMobile = useIsMobile()
  const navigate = useNavigate()

  const services = [
    {
      title: "Lead Generation",
      description: "AI-powered lead generation that finds your perfect prospects",
      icon: "💡",
      path: "/lead-generation"
    },
    {
      title: "Lead Qualification",
      description: "Smart filtering to focus on high-quality leads",
      icon: "✨",
      path: "/lead-qualification"
    },
    {
      title: "Sales Automation",
      description: "Automated outreach that feels personal and genuine",
      icon: "🎯",
      path: "/sales-automation"
    },
    {
      title: "Client Management",
      description: "Seamless client relationship management and support",
      icon: "🤝",
      path: "/client-management"
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-b from-gray-50 to-white">
      {/* Hero Section */}
      <section className="container mx-auto px-4 pt-20 pb-16 text-center">
        <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
          Perfect Fit Digital Marketing Agency
        </h1>
        <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto">
          AI-Powered Marketing Solutions That Adapt to Your Business
        </p>
        <div className="flex flex-col md:flex-row gap-4 justify-center">
          <Link to="/lead-generation">
            <Button 
              size="lg" 
              className="bg-blue-600 hover:bg-blue-700 w-full"
            >
              Get Started
            </Button>
          </Link>
          <Button 
            size="lg" 
            variant="outline"
            asChild
            onClick={() => {
              const contactSection = document.querySelector('#contact-form')
              if (contactSection) {
                contactSection.scrollIntoView({ behavior: 'smooth' })
              }
            }}
          >
            <button>Book a Demo</button>
          </Button>
        </div>
      </section>

      {/* Services Grid */}
      <section className="container mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-center mb-12">Our Services</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {services.map((service, index) => (
            <Link to={service.path} key={index} className="block">
              <Card className="hover:shadow-lg transition-shadow cursor-pointer h-full">
                <CardHeader>
                  <div className="text-4xl mb-4">{service.icon}</div>
                  <CardTitle>{service.title}</CardTitle>
                  <CardDescription>{service.description}</CardDescription>
                </CardHeader>
                <CardContent>
                  <Button variant="ghost" className="w-full">Learn More →</Button>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      {/* Why Choose Us */}
      <section className="container mx-auto px-4 py-16 bg-gray-50">
        <h2 className="text-3xl font-bold text-center mb-12">Why Choose Perfect Fit?</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Card>
            <CardContent className="pt-6">
              <h3 className="text-xl font-semibold mb-2">AI-Powered Insights</h3>
              <p className="text-gray-600">
                Our AI algorithms analyze market trends and customer behavior to deliver actionable insights.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <h3 className="text-xl font-semibold mb-2">Personalized Approach</h3>
              <p className="text-gray-600">
                Every business is unique. We tailor our solutions to fit your specific needs and goals.
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <h3 className="text-xl font-semibold mb-2">Proven Results</h3>
              <p className="text-gray-600">
                Track your success with real-time analytics and transparent reporting.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="container mx-auto px-4 py-16 text-center">
        <Card className="bg-blue-600 text-white p-8">
          <CardContent>
            <h2 className="text-3xl font-bold mb-4">Ready to Transform Your Marketing?</h2>
            <p className="text-xl mb-6">
              Join businesses that are growing with AI-powered marketing solutions.
            </p>
            <Link to="/lead-generation">
              <Button 
                size="lg" 
                variant="secondary" 
                className="bg-white text-blue-600 hover:bg-gray-100 w-full"
              >
                Start Your Journey
              </Button>
            </Link>
          </CardContent>
        </Card>
      </section>

      {/* Contact Form */}
      <section id="contact-form" className="container mx-auto px-4 py-16">
        <Card className="max-w-2xl mx-auto">
          <CardHeader>
            <CardTitle className="text-2xl text-center">Contact Us</CardTitle>
            <CardDescription className="text-center">
              Ready to get started? Send us a message and we'll get back to you within 24 hours.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={(e) => {
              e.preventDefault()
              // Handle form submission
              const formData = new FormData(e.target)
              console.log(Object.fromEntries(formData))
              alert('Thank you for your message! We will get back to you soon.')
              e.target.reset()
            }} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label htmlFor="name" className="text-sm font-medium">Name</label>
                  <Input id="name" name="name" placeholder="Your name" required />
                </div>
                <div className="space-y-2">
                  <label htmlFor="email" className="text-sm font-medium">Email</label>
                  <Input id="email" name="email" type="email" placeholder="your@email.com" required />
                </div>
              </div>
              <div className="space-y-2">
                <label htmlFor="company" className="text-sm font-medium">Company</label>
                <Input id="company" name="company" placeholder="Your company name" />
              </div>
              <div className="space-y-2">
                <label htmlFor="message" className="text-sm font-medium">Message</label>
                <Textarea
                  id="message"
                  name="message"
                  placeholder="Tell us about your project..."
                  className="min-h-[100px]"
                  required
                />
              </div>
              <Button type="submit" className="w-full">Send Message</Button>
            </form>
          </CardContent>
        </Card>
      </section>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 border-t">
        <div className="text-center text-gray-600">
          <p>© 2025 Perfect Fit Digital Marketing Agency. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage