import React, { useState, useEffect } from 'react';
import { 
  AppShell, 
  Navbar, 
  Header, 
  Text, 
  MediaQuery, 
  Burger, 
  useMantineTheme, 
  Group, 
  Title, 
  Avatar, 
  ActionIcon, 
  Grid, 
  Card, 
  Badge, 
  Stack, 
  Button, 
  Progress, 
  Table, 
  ScrollArea,
  Divider,
  SimpleGrid,
  RingProgress,
  Center,
  Paper
} from '@mantine/core';
import { 
  IconBell, 
  IconSettings, 
  IconChartBar, 
  IconUsers, 
  IconBrandCampaignmonitor, 
  IconRobot, 
  IconFileText, 
  IconCalendarStats, 
  IconWorld,
  IconPlus,
  IconArrowUp,
  IconArrowDown,
  IconClockHour4,
  IconCheck,
  IconX
} from '@tabler/icons-react';
import { useNavigate } from 'react-router-dom';
import { MainNavbar } from './MainNavbar';
import { format } from 'date-fns';

// Types
interface AgentStatus {
  [key: string]: 'active' | 'idle' | 'error';
}

interface Campaign {
  id: string;
  name: string;
  status: 'active' | 'completed' | 'planned';
  startDate: string;
  endDate: string;
  progress: number;
  contentItems: number;
}

interface Activity {
  id: string;
  timestamp: string;
  agent: string;
  action: string;
  status: 'completed' | 'in_progress' | 'failed';
}

interface ContentItem {
  id: string;
  type: string;
  title: string;
  status: 'draft' | 'review' | 'approved' | 'published';
  createdAt: string;
}

interface DashboardMetrics {
  activeCampaigns: number;
  pendingContentItems: number;
  completedContentItems: number;
  agentStatus: Record<string, string>;
  recentActivities: Activity[];
}

// Mock data
const mockAgentStatus: AgentStatus = {
  'market_research': 'active',
  'icp_discovery': 'idle',
  'campaign_planning': 'active',
  'content_generation': 'active',
  'localization': 'active',
  'scheduler': 'idle',
  'outreach': 'active',
  'master_controller': 'active'
};

const mockCampaigns: Campaign[] = [
  {
    id: 'camp1',
    name: 'Summer Fitness Tracker Launch',
    status: 'active',
    startDate: '2023-06-01',
    endDate: '2023-08-31',
    progress: 45,
    contentItems: 12
  },
  {
    id: 'camp2',
    name: 'Back to School Promotion',
    status: 'planned',
    startDate: '2023-07-15',
    endDate: '2023-09-15',
    progress: 10,
    contentItems: 5
  },
  {
    id: 'camp3',
    name: 'Spring Product Launch',
    status: 'completed',
    startDate: '2023-05-01',
    endDate: '2023-05-31',
    progress: 100,
    contentItems: 25
  }
];

const mockActivities: Activity[] = [
  {
    id: 'act1',
    timestamp: new Date().toISOString(),
    agent: 'content_generation',
    action: 'Generated social media post for Summer Fitness Tracker',
    status: 'completed'
  },
  {
    id: 'act2',
    timestamp: new Date(Date.now() - 30 * 60000).toISOString(),
    agent: 'localization',
    action: 'Translated content to Spanish and French',
    status: 'completed'
  },
  {
    id: 'act3',
    timestamp: new Date(Date.now() - 60 * 60000).toISOString(),
    agent: 'market_research',
    action: 'Analyzed market trends for fitness trackers',
    status: 'completed'
  },
  {
    id: 'act4',
    timestamp: new Date(Date.now() - 90 * 60000).toISOString(),
    agent: 'outreach',
    action: 'Scheduled email campaign for Summer Fitness Tracker',
    status: 'in_progress'
  },
  {
    id: 'act5',
    timestamp: new Date(Date.now() - 120 * 60000).toISOString(),
    agent: 'icp_discovery',
    action: 'Identified target audience for Back to School Promotion',
    status: 'failed'
  }
];

const mockContentItems: ContentItem[] = [
  {
    id: 'cont1',
    type: 'social_post',
    title: 'Summer Fitness Challenge Announcement',
    status: 'published',
    createdAt: new Date(Date.now() - 2 * 24 * 60 * 60000).toISOString()
  },
  {
    id: 'cont2',
    type: 'email',
    title: 'Fitness Tracker Launch Email',
    status: 'review',
    createdAt: new Date(Date.now() - 1 * 24 * 60 * 60000).toISOString()
  },
  {
    id: 'cont3',
    type: 'ad_copy',
    title: 'Facebook Ad for Fitness Tracker',
    status: 'draft',
    createdAt: new Date().toISOString()
  }
];

// Component
export function Dashboard() {
  const theme = useMantineTheme();
  const [opened, setOpened] = useState(false);
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  // Fetch dashboard data
  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        // In a real implementation, this would be an API call
        // const response = await fetch('/api/dashboard');
        // const data = await response.json();
        
        // Using mock data for now
        setMetrics({
          activeCampaigns: 3,
          pendingContentItems: 12,
          completedContentItems: 45,
          agentStatus: mockAgentStatus,
          recentActivities: mockActivities
        });
        
        setLoading(false);
      } catch (error) {
        console.error('Error fetching dashboard data:', error);
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'green';
      case 'idle':
        return 'blue';
      case 'error':
        return 'red';
      case 'completed':
        return 'green';
      case 'in_progress':
        return 'blue';
      case 'failed':
        return 'red';
      case 'published':
        return 'green';
      case 'review':
        return 'yellow';
      case 'draft':
        return 'blue';
      case 'approved':
        return 'teal';
      default:
        return 'gray';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
      case 'published':
      case 'approved':
        return <IconCheck size={16} />;
      case 'in_progress':
      case 'review':
      case 'draft':
        return <IconClockHour4 size={16} />;
      case 'failed':
        return <IconX size={16} />;
      default:
        return null;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      return format(new Date(timestamp), 'MMM d, h:mm a');
    } catch (e) {
      return timestamp;
    }
  };

  return (
    <AppShell
      padding="md"
      navbar={
        <Navbar p="md" hiddenBreakpoint="sm" hidden={!opened} width={{ sm: 200, lg: 250 }}>
          <MainNavbar />
        </Navbar>
      }
      header={
        <Header height={60} p="xs">
          <Group sx={{ height: '100%' }} px={20} position="apart">
            <MediaQuery largerThan="sm" styles={{ display: 'none' }}>
              <Burger
                opened={opened}
                onClick={() => setOpened((o) => !o)}
                size="sm"
                color={theme.colors.gray[6]}
                mr="xl"
              />
            </MediaQuery>

            <Group>
              <Title order={3} color={theme.primaryColor}>Catalyst Marketing Platform</Title>
            </Group>

            <Group>
              <ActionIcon variant="default" size={30}>
                <IconBell size={16} />
              </ActionIcon>
              <ActionIcon variant="default" size={30}>
                <IconSettings size={16} />
              </ActionIcon>
              <Avatar color="blue" radius="xl">JD</Avatar>
            </Group>
          </Group>
        </Header>
      }
      styles={(theme) => ({
        main: { backgroundColor: theme.colorScheme === 'dark' ? theme.colors.dark[8] : theme.colors.gray[0] },
      })}
    >
      {/* Dashboard Content */}
      <Stack spacing="lg">
        {/* Stats Overview */}
        <SimpleGrid cols={4} breakpoints={[{ maxWidth: 'sm', cols: 1 }, { maxWidth: 'md', cols: 2 }]}>
          <Card withBorder p="md" radius="md">
            <Group position="apart">
              <Text size="xs" color="dimmed" weight={700} transform="uppercase">
                Active Campaigns
              </Text>
              <ActionIcon color="blue" variant="light">
                <IconBrandCampaignmonitor size={18} />
              </ActionIcon>
            </Group>
            <Group position="apart" mt="xs">
              <Text size="xl" weight={700}>
                {metrics?.activeCampaigns || 0}
              </Text>
              <Badge color="green" variant="light">
                +2 this month
              </Badge>
            </Group>
            <Text size="xs" color="dimmed" mt="md">
              <span style={{ color: theme.colors.green[6] }}>
                <IconArrowUp size={12} /> 12%
              </span>{' '}
              increase compared to last month
            </Text>
          </Card>

          <Card withBorder p="md" radius="md">
            <Group position="apart">
              <Text size="xs" color="dimmed" weight={700} transform="uppercase">
                Pending Content
              </Text>
              <ActionIcon color="yellow" variant="light">
                <IconFileText size={18} />
              </ActionIcon>
            </Group>
            <Group position="apart" mt="xs">
              <Text size="xl" weight={700}>
                {metrics?.pendingContentItems || 0}
              </Text>
              <Badge color="yellow" variant="light">
                Needs attention
              </Badge>
            </Group>
            <Text size="xs" color="dimmed" mt="md">
              <span style={{ color: theme.colors.red[6] }}>
                <IconArrowUp size={12} /> 5%
              </span>{' '}
              increase in pending items
            </Text>
          </Card>

          <Card withBorder p="md" radius="md">
            <Group position="apart">
              <Text size="xs" color="dimmed" weight={700} transform="uppercase">
                Completed Content
              </Text>
              <ActionIcon color="green" variant="light">
                <IconCheck size={18} />
              </ActionIcon>
            </Group>
            <Group position="apart" mt="xs">
              <Text size="xl" weight={700}>
                {metrics?.completedContentItems || 0}
              </Text>
              <Badge color="green" variant="light">
                On track
              </Badge>
            </Group>
            <Text size="xs" color="dimmed" mt="md">
              <span style={{ color: theme.colors.green[6] }}>
                <IconArrowUp size={12} /> 23%
              </span>{' '}
              increase compared to last month
            </Text>
          </Card>

          <Card withBorder p="md" radius="md">
            <Group position="apart">
              <Text size="xs" color="dimmed" weight={700} transform="uppercase">
                Active Agents
              </Text>
              <ActionIcon color="blue" variant="light">
                <IconRobot size={18} />
              </ActionIcon>
            </Group>
            <Group position="apart" mt="xs">
              <Text size="xl" weight={700}>
                {Object.values(metrics?.agentStatus || {}).filter(status => status === 'active').length || 0}
              </Text>
              <Badge color="blue" variant="light">
                {Object.keys(metrics?.agentStatus || {}).length || 0} total
              </Badge>
            </Group>
            <Text size="xs" color="dimmed" mt="md">
              All critical agents are operational
            </Text>
          </Card>
        </SimpleGrid>

        {/* Main Content Grid */}
        <Grid gutter="md">
          {/* Campaigns Section */}
          <Grid.Col xs={12} md={6}>
            <Card withBorder p="md" radius="md">
              <Group position="apart" mb="xs">
                <Text weight={700}>Active Campaigns</Text>
                <Button 
                  variant="light" 
                  leftIcon={<IconPlus size={14} />} 
                  size="xs"
                  onClick={() => navigate('/campaigns/new')}
                >
                  New Campaign
                </Button>
              </Group>
              
              <ScrollArea style={{ height: 300 }}>
                <Stack spacing="xs">
                  {mockCampaigns.map((campaign) => (
                    <Paper 
                      key={campaign.id} 
                      p="md" 
                      withBorder 
                      sx={{ cursor: 'pointer' }}
                      onClick={() => navigate(`/campaigns/${campaign.id}`)}
                    >
                      <Group position="apart">
                        <div>
                          <Text weight={600}>{campaign.name}</Text>
                          <Text size="xs" color="dimmed">
                            {campaign.startDate} to {campaign.endDate}
                          </Text>
                        </div>
                        <Badge 
                          color={
                            campaign.status === 'active' ? 'green' : 
                            campaign.status === 'planned' ? 'blue' : 'gray'
                          }
                        >
                          {campaign.status}
                        </Badge>
                      </Group>
                      <Text size="xs" mt="xs">Progress:</Text>
                      <Progress 
                        value={campaign.progress} 
                        mt={5} 
                        size="sm" 
                        color={campaign.progress === 100 ? 'green' : 'blue'} 
                      />
                      <Group position="apart" mt="xs">
                        <Text size="xs" color="dimmed">{campaign.contentItems} content items</Text>
                        <Text size="xs" color="dimmed">{campaign.progress}% complete</Text>
                      </Group>
                    </Paper>
                  ))}
                </Stack>
              </ScrollArea>
            </Card>
          </Grid.Col>

          {/* Agent Status Section */}
          <Grid.Col xs={12} md={6}>
            <Card withBorder p="md" radius="md">
              <Group position="apart" mb="xs">
                <Text weight={700}>Agent Status</Text>
                <Button 
                  variant="subtle" 
                  size="xs"
                  onClick={() => navigate('/agents')}
                >
                  View All
                </Button>
              </Group>
              
              <ScrollArea style={{ height: 300 }}>
                <Table>
                  <thead>
                    <tr>
                      <th>Agent</th>
                      <th>Status</th>
                      <th>Load</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(mockAgentStatus).map(([agent, status]) => (
                      <tr key={agent}>
                        <td>
                          <Group spacing="sm">
                            <IconRobot size={16} />
                            <Text>{agent.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}</Text>
                          </Group>
                        </td>
                        <td>
                          <Badge 
                            color={getStatusColor(status)}
                            size="sm"
                          >
                            {status}
                          </Badge>
                        </td>
                        <td>
                          <RingProgress
                            size={24}
                            thickness={3}
                            sections={[
                              { 
                                value: status === 'active' ? Math.floor(Math.random() * 80) + 20 : 0, 
                                color: status === 'active' ? 'blue' : 'gray' 
                              },
                            ]}
                          />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </ScrollArea>
            </Card>
          </Grid.Col>

          {/* Recent Activity Section */}
          <Grid.Col xs={12} md={6}>
            <Card withBorder p="md" radius="md">
              <Text weight={700} mb="xs">Recent Activity</Text>
              
              <ScrollArea style={{ height: 300 }}>
                <Stack spacing="xs">
                  {mockActivities.map((activity) => (
                    <Paper key={activity.id} p="sm" withBorder>
                      <Group position="apart" mb={5}>
                        <Text size="sm" weight={500}>
                          {activity.agent.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                        </Text>
                        <Text size="xs" color="dimmed">
                          {formatTimestamp(activity.timestamp)}
                        </Text>
                      </Group>
                      <Text size="sm">{activity.action}</Text>
                      <Group position="right" mt={5}>
                        <Badge 
                          size="sm"
                          color={getStatusColor(activity.status)}
                          leftSection={getStatusIcon(activity.status)}
                        >
                          {activity.status.replace('_', ' ')}
                        </Badge>
                      </Group>
                    </Paper>
                  ))}
                </Stack>
              </ScrollArea>
            </Card>
          </Grid.Col>

          {/* Recent Content Section */}
          <Grid.Col xs={12} md={6}>
            <Card withBorder p="md" radius="md">
              <Group position="apart" mb="xs">
                <Text weight={700}>Recent Content</Text>
                <Button 
                  variant="light" 
                  leftIcon={<IconPlus size={14} />} 
                  size="xs"
                  onClick={() => navigate('/content/new')}
                >
                  Create Content
                </Button>
              </Group>
              
              <ScrollArea style={{ height: 300 }}>
                <Table>
                  <thead>
                    <tr>
                      <th>Title</th>
                      <th>Type</th>
                      <th>Status</th>
                      <th>Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {mockContentItems.map((item) => (
                      <tr key={item.id} style={{ cursor: 'pointer' }} onClick={() => navigate(`/content/${item.id}`)}>
                        <td>
                          <Text size="sm">{item.title}</Text>
                        </td>
                        <td>
                          <Badge size="sm" variant="outline">
                            {item.type.replace('_', ' ')}
                          </Badge>
                        </td>
                        <td>
                          <Badge 
                            size="sm"
                            color={getStatusColor(item.status)}
                          >
                            {item.status}
                          </Badge>
                        </td>
                        <td>
                          <Text size="xs" color="dimmed">
                            {formatTimestamp(item.createdAt)}
                          </Text>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </ScrollArea>
            </Card>
          </Grid.Col>
        </Grid>

        {/* Quick Actions */}
        <SimpleGrid cols={4} breakpoints={[{ maxWidth: 'sm', cols: 2 }, { maxWidth: 'xs', cols: 1 }]}>
          <Button 
            variant="light" 
            leftIcon={<IconFileText />}
            onClick={() => navigate('/content/new')}
            fullWidth
          >
            Create Content
          </Button>
          <Button 
            variant="light" 
            leftIcon={<IconBrandCampaignmonitor />}
            onClick={() => navigate('/campaigns/new')}
            fullWidth
          >
            New Campaign
          </Button>
          <Button 
            variant="light" 
            leftIcon={<IconWorld />}
            onClick={() => navigate('/localization')}
            fullWidth
          >
            Localize Content
          </Button>
          <Button 
            variant="light" 
            leftIcon={<IconChartBar />}
            onClick={() => navigate('/analytics')}
            fullWidth
          >
            View Analytics
          </Button>
        </SimpleGrid>
      </Stack>
    </AppShell>
  );
}
