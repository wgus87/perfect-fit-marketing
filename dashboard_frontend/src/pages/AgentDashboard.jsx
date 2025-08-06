import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs';
import { Badge } from '../components/ui/badge';

const AgentDashboard = () => {
  const [leads, setLeads] = useState([]);
  const [chats, setChats] = useState([]);
  const [activeTab, setActiveTab] = useState('leads');
  const [selectedLead, setSelectedLead] = useState(null);
  const [loading, setLoading] = useState(true);
  const agentId = 'agent123'; // This should come from authentication

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [leadsResponse, chatsResponse] = await Promise.all([
        fetch(`http://localhost:5000/api/agents/${agentId}/leads`),
        fetch('http://localhost:5000/api/chat/unresolved')
      ]);

      const [leadsData, chatsData] = await Promise.all([
        leadsResponse.json(),
        chatsResponse.json()
      ]);

      setLeads(leadsData);
      setChats(chatsData);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleLeadStatusUpdate = async (leadId, status) => {
    try {
      await fetch(`http://localhost:5000/api/leads/${leadId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ status })
      });
      
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Error updating lead status:', error);
    }
  };

  const handleAddNote = async (leadId, note) => {
    try {
      await fetch(`http://localhost:5000/api/leads/${leadId}/notes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ notes: note, agent_id: agentId })
      });
      
      fetchData(); // Refresh data
    } catch (error) {
      console.error('Error adding note:', error);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
      >
        <div className="max-w-7xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-8">Agent Dashboard</h1>
          
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">{leads.length}</div>
                <div className="text-sm text-gray-600">Active Leads</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">
                  {leads.filter(l => l.status === 'qualified').length}
                </div>
                <div className="text-sm text-gray-600">Qualified Leads</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">{chats.length}</div>
                <div className="text-sm text-gray-600">Open Chats</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-2xl font-bold">
                  {leads.filter(l => l.lead_score >= 80).length}
                </div>
                <div className="text-sm text-gray-600">High Priority</div>
              </CardContent>
            </Card>
          </div>

          <Tabs defaultValue="leads" className="w-full">
            <TabsList>
              <TabsTrigger value="leads">Leads</TabsTrigger>
              <TabsTrigger value="chats">Active Chats</TabsTrigger>
              <TabsTrigger value="activities">Recent Activities</TabsTrigger>
            </TabsList>

            <TabsContent value="leads">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {leads.map(lead => (
                  <Card key={lead.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle>{lead.name}</CardTitle>
                          <CardDescription>{lead.email}</CardDescription>
                        </div>
                        <Badge
                          variant={lead.lead_score >= 80 ? 'destructive' : 'default'}
                        >
                          Score: {lead.lead_score}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div>
                          <div className="text-sm font-medium">Company</div>
                          <div className="text-gray-600">{lead.company}</div>
                        </div>
                        <div>
                          <div className="text-sm font-medium">Status</div>
                          <select
                            value={lead.status}
                            onChange={(e) => handleLeadStatusUpdate(lead.id, e.target.value)}
                            className="mt-1 block w-full py-2 px-3 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                          >
                            <option value="new">New</option>
                            <option value="contacted">Contacted</option>
                            <option value="qualified">Qualified</option>
                            <option value="proposal">Proposal</option>
                            <option value="closed">Closed</option>
                          </select>
                        </div>
                        <div>
                          <div className="text-sm font-medium">Notes</div>
                          <div className="mt-2">
                            <textarea
                              className="w-full px-3 py-2 border rounded-md"
                              rows="3"
                              placeholder="Add a note..."
                              onBlur={(e) => {
                                if (e.target.value) {
                                  handleAddNote(lead.id, e.target.value);
                                  e.target.value = '';
                                }
                              }}
                            />
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="chats">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {chats.map(chat => (
                  <Card key={chat.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <CardTitle>Chat #{chat.id}</CardTitle>
                      <CardDescription>User ID: {chat.user_id}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-4">
                        <div>
                          <div className="text-sm font-medium">Last Message</div>
                          <div className="text-gray-600">{chat.message}</div>
                        </div>
                        <div>
                          <div className="text-sm font-medium">Sentiment</div>
                          <Badge variant={chat.sentiment > 0 ? 'success' : 'destructive'}>
                            {chat.sentiment > 0 ? 'Positive' : 'Negative'}
                          </Badge>
                        </div>
                        <Button
                          onClick={() => {
                            // Handle chat resolution
                          }}
                        >
                          Resolve Chat
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>

            <TabsContent value="activities">
              <Card>
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    {leads.flatMap(lead => lead.activities || []).sort((a, b) => 
                      new Date(b.timestamp) - new Date(a.timestamp)
                    ).map(activity => (
                      <div key={activity.id} className="flex items-start space-x-4">
                        <div className="min-w-0 flex-1">
                          <p className="text-sm font-medium text-gray-900">
                            {activity.activity_type}
                          </p>
                          <p className="text-sm text-gray-500">
                            {activity.description}
                          </p>
                          <p className="text-xs text-gray-400">
                            {new Date(activity.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>
      </motion.div>
    </div>
  );
};

export default AgentDashboard;
