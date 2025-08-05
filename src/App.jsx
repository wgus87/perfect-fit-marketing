import './App.css'
import LandingPage from './components/LandingPage'

function App() {
  return (
    <div className="App">
      <LandingPage />
    </div>
  )
}
  const [overview, setOverview] = useState(null)
  const [leads, setLeads] = useState([])
  const [pipeline, setPipeline] = useState([])
  const [clients, setClients] = useState([])
  const [analytics, setAnalytics] = useState(null)
  const [agentPerformance, setAgentPerformance] = useState([])
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      
      // Fetch all dashboard data
      const [overviewRes, leadsRes, pipelineRes, clientsRes, analyticsRes, agentsRes, tasksRes] = await Promise.all([
        fetch('/api/dashboard/overview'),
        fetch('/api/dashboard/leads?per_page=5'),
        fetch('/api/dashboard/pipeline'),
        fetch('/api/dashboard/clients'),
        fetch('/api/dashboard/analytics'),
        fetch('/api/dashboard/agent-performance'),
        fetch('/api/dashboard/tasks')
      ])

      const overviewData = await overviewRes.json()
      const leadsData = await leadsRes.json()
      const pipelineData = await pipelineRes.json()
      const clientsData = await clientsRes.json()
      const analyticsData = await analyticsRes.json()
      const agentsData = await agentsRes.json()
      const tasksData = await tasksRes.json()

      setOverview(overviewData)
      setLeads(leadsData.leads || [])
      setPipeline(pipelineData.pipeline || [])
      setClients(clientsData.clients || [])
      setAnalytics(analyticsData)
      setAgentPerformance(agentsData.agents || [])
      setTasks(tasksData.tasks || [])
      
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading dashboard...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div className="flex items-center">
              <Bot className="h-8 w-8 text-blue-600 mr-3" />
              <div>
                <h1 className="text-2xl font-bold text-gray-900">AI Marketing Agency</h1>
                <p className="text-sm text-gray-500">Automated Lead Generation & Sales</p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
                <Activity className="h-3 w-3 mr-1" />
                All Systems Active
              </Badge>
              <Button onClick={fetchDashboardData} variant="outline" size="sm">
                Refresh
              </Button>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <Card className="bg-gradient-to-r from-blue-500 to-blue-600 text-white">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Leads</CardTitle>
              <Users className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview?.leads?.total || 0}</div>
              <p className="text-xs text-blue-100">
                {overview?.leads?.qualified || 0} qualified ({overview?.leads?.conversion_rate || 0}%)
              </p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-r from-green-500 to-green-600 text-white">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Pipeline Value</CardTitle>
              <DollarSign className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${(overview?.sales?.pipeline_value || 0).toLocaleString()}</div>
              <p className="text-xs text-green-100">
                {overview?.sales?.active_deals || 0} active deals
              </p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-r from-purple-500 to-purple-600 text-white">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Monthly Revenue</CardTitle>
              <TrendingUp className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">${(overview?.clients?.monthly_revenue || 0).toLocaleString()}</div>
              <p className="text-xs text-purple-100">
                {overview?.clients?.active || 0} active clients
              </p>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-r from-orange-500 to-orange-600 text-white">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Response Rate</CardTitle>
              <Mail className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{overview?.outreach?.response_rate || 0}%</div>
              <p className="text-xs text-orange-100">
                {overview?.outreach?.total_replies || 0} of {overview?.outreach?.total_sent || 0} sent
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Main Content Tabs */}
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList className="grid w-full grid-cols-5">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="leads">Leads</TabsTrigger>
            <TabsTrigger value="pipeline">Pipeline</TabsTrigger>
            <TabsTrigger value="clients">Clients</TabsTrigger>
            <TabsTrigger value="agents">AI Agents</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Lead Generation Chart */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <BarChart3 className="h-5 w-5 mr-2" />
                    Lead Generation Trend
                  </CardTitle>
                  <CardDescription>Daily lead generation over the last 30 days</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={analytics?.lead_generation?.slice(-14) || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip />
                      <Area type="monotone" dataKey="leads" stackId="1" stroke="#3B82F6" fill="#3B82F6" fillOpacity={0.6} />
                      <Area type="monotone" dataKey="qualified" stackId="1" stroke="#10B981" fill="#10B981" fillOpacity={0.6} />
                    </AreaChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Revenue Chart */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <TrendingUp className="h-5 w-5 mr-2" />
                    Revenue Growth
                  </CardTitle>
                  <CardDescription>Cumulative revenue over time</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={analytics?.revenue?.slice(-14) || []}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" />
                      <YAxis />
                      <Tooltip formatter={(value) => [`$${value.toLocaleString()}`, 'Revenue']} />
                      <Line type="monotone" dataKey="cumulative_revenue" stroke="#8B5CF6" strokeWidth={3} />
                    </LineChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Recent Activity */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Activity className="h-5 w-5 mr-2" />
                  Recent Tasks & Activities
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {tasks.slice(0, 5).map((task, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <div className={`h-2 w-2 rounded-full ${
                          task.status === 'completed' ? 'bg-green-500' : 
                          task.status === 'in_progress' ? 'bg-blue-500' : 'bg-gray-400'
                        }`} />
                        <div>
                          <p className="font-medium text-sm">{task.title}</p>
                          <p className="text-xs text-gray-500">{task.company_name}</p>
                        </div>
                      </div>
                      <Badge variant={task.status === 'completed' ? 'default' : 'secondary'}>
                        {task.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="leads" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Recent Leads</CardTitle>
                <CardDescription>Latest leads generated by the AI system</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {leads.map((lead, index) => (
                    <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
                      <div className="flex items-center space-x-4">
                        <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
                          <Users className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium">{lead.company_name}</p>
                          <p className="text-sm text-gray-500">{lead.contact_name} • {lead.industry}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge variant={lead.qualification_status === 'qualified' ? 'default' : 'secondary'}>
                          {lead.qualification_status || 'pending'}
                        </Badge>
                        <p className="text-xs text-gray-500 mt-1">Score: {lead.total_score || 'N/A'}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="pipeline" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Sales Pipeline</CardTitle>
                    <CardDescription>Active deals and their progress</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {pipeline.map((deal, index) => (
                        <div key={index} className="p-4 border rounded-lg">
                          <div className="flex justify-between items-start mb-2">
                            <div>
                              <p className="font-medium">{deal.company_name}</p>
                              <p className="text-sm text-gray-500">{deal.contact_name}</p>
                            </div>
                            <div className="text-right">
                              <p className="font-bold">${deal.value?.toLocaleString()}</p>
                              <Badge variant="outline">{deal.stage?.replace('_', ' ')}</Badge>
                            </div>
                          </div>
                          <Progress value={(deal.probability || 0) * 100} className="h-2" />
                          <p className="text-xs text-gray-500 mt-1">{Math.round((deal.probability || 0) * 100)}% probability</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <PieChartIcon className="h-5 w-5 mr-2" />
                    Pipeline Distribution
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={200}>
                    <PieChart>
                      <Pie
                        data={pipeline.reduce((acc, deal) => {
                          const stage = deal.stage?.replace('_', ' ') || 'unknown'
                          const existing = acc.find(item => item.name === stage)
                          if (existing) {
                            existing.value += 1
                          } else {
                            acc.push({ name: stage, value: 1 })
                          }
                          return acc
                        }, [])}
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                        label
                      >
                        {pipeline.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="clients" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Active Clients</CardTitle>
                <CardDescription>Current client portfolio and status</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {clients.map((client, index) => (
                    <Card key={index} className="p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <p className="font-medium">{client.company_name}</p>
                          <p className="text-sm text-gray-500">{client.contact_name}</p>
                        </div>
                        <Badge variant={client.status === 'active' ? 'default' : 'secondary'}>
                          {client.status}
                        </Badge>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Package:</span>
                          <span className="font-medium">{client.package}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span>Monthly Value:</span>
                          <span className="font-medium">${client.monthly_value?.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span>Satisfaction:</span>
                          <span className="font-medium">{client.satisfaction_score || 'N/A'}/5.0</span>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="agents" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Bot className="h-5 w-5 mr-2" />
                  AI Agent Performance
                </CardTitle>
                <CardDescription>Real-time performance metrics for all AI agents</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {agentPerformance.map((agent, index) => (
                    <Card key={index} className="p-4">
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center space-x-2">
                          <Zap className="h-4 w-4 text-blue-600" />
                          <p className="font-medium text-sm">{agent.name}</p>
                        </div>
                        <Badge variant={agent.status === 'active' ? 'default' : 'secondary'}>
                          {agent.status}
                        </Badge>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>{agent.metric}:</span>
                          <span className="font-bold">{agent.value}</span>
                        </div>
                        <div>
                          <div className="flex justify-between text-xs mb-1">
                            <span>Efficiency:</span>
                            <span>{agent.efficiency}%</span>
                          </div>
                          <Progress value={agent.efficiency} className="h-2" />
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

export default App

