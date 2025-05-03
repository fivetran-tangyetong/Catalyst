import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  Container,
  Grid,
  LoadingOverlay,
  Paper,
  Stack,
  Stepper,
  Text,
  TextInput,
  Title,
  useMantineTheme,
  MultiSelect,
  Modal,
  Select,
  Group,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { IconPhone, IconArrowRight, IconCheck } from '@tabler/icons-react';
import {
  translateText,
  makeVapiCall,
  listVapiAssistants,
  analyzeTrends,
} from '../services/mcpService.tsx';
import { useNavigate } from 'react-router-dom';

export function ContentCreator() {
  const theme = useMantineTheme();
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [generatedBody, setGeneratedBody] = useState('');
  const [localized, setLocalized] = useState<Record<string, string>>({});
  const [assistants, setAssistants] = useState<{ id: string; name: string }[]>([]);
  const [callModal, setCallModal] = useState(false);
  const [callPhone, setCallPhone] = useState('');
  const [selectedAssistant, setSelectedAssistant] = useState<string | null>('');

  const form = useForm({
    initialValues: {
      title: '',
      productName: '',
      benefit: '',
      targetLanguages: [] as string[],
    },
    validate: {
      title: (v) => (v ? null : 'Title is required'),
      productName: (v) => (v ? null : 'Product is required'),
    },
  });

  useEffect(() => {
    listVapiAssistants().then((list) => {
      setAssistants(list.map((a: any) => ({ id: a.id, name: a.name || a.id })));
      if (list.length) setSelectedAssistant(list[0].id);
    });
  }, []);

  const handleGenerate = () => {
    const errors = form.validate();
    if (errors.hasErrors) return;
    const body = `Introducing ${form.values.productName}, it helps you ${form.values.benefit}.`;
    setGeneratedBody(body);
    setActiveStep(1);
  };

  const handleApproveAndPlan = async () => {
    setLoading(true);
    try {
      const loc: Record<string, string> = {};
      for (const lang of form.values.targetLanguages) {
        const res = await translateText({ text: generatedBody, target_lang: lang });
        loc[lang] = res.translations[0].text;
      }
      setLocalized(loc);

      if (selectedAssistant && callPhone) {
        await makeVapiCall(selectedAssistant, callPhone, generatedBody);
      }

      const trends = await analyzeTrends({ product_category: form.values.productName, timeframe: 'last 30 days' });
      notifications.show({ title: 'Campaign Plan', message: `Top trend: ${trends.summary}`, color: 'blue' });
      notifications.show({ title: 'Done', message: 'Content approved & campaign planned', color: 'green', icon: <IconCheck /> });
      navigate('/content');
    } catch (error: any) {
      notifications.show({ title: 'Error', message: error.message, color: 'red' });
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container size="sm" py="xl">
      <Stepper active={activeStep} onStepClick={setActiveStep} breakpoint="sm">
        <Stepper.Step label="Write" icon={<IconArrowRight size={18} />}>
          <Stack spacing="md">
            <TextInput label="Title" placeholder="Your title" {...form.getInputProps('title')} />
            <TextInput label="Product" placeholder="Your product" {...form.getInputProps('productName')} />
            <TextInput label="Benefit" placeholder="Key benefit" {...form.getInputProps('benefit')} />
            <MultiSelect
              label="Translate to"
              placeholder="Select languages"
              data={[
                { value: 'es', label: 'Spanish' },
                { value: 'fr', label: 'French' },
                { value: 'de', label: 'German' },
                { value: 'en', label: 'English' },
                { value: 'cm', label: 'Chinese' },
              ]}
              {...form.getInputProps('targetLanguages')}
            />
            <Group position="right">
              <Button onClick={handleGenerate}>Generate</Button>
            </Group>
          </Stack>
        </Stepper.Step>

        <Stepper.Step label="Review" icon={<IconCheck size={18} />}>
          <Box pos="relative">
            <LoadingOverlay visible={loading} overlayBlur={2} />
            <Stack spacing="lg">
              <Title order={4}>{form.values.title}</Title>
              <Text>{generatedBody}</Text>

              {Object.entries(localized).map(([lang, text]) => (
                <Card key={lang} shadow="sm" p="md">
                  <Text weight={600}>{lang.toUpperCase()}</Text>
                  <Text>{text}</Text>
                </Card>
              ))}

              <Card shadow="xs" p="md">
                <Select
                  label="Select Assistant"
                  placeholder="Choose..."
                  data={assistants.map((a) => ({ value: a.id, label: a.name }))}
                  value={selectedAssistant}
                  onChange={setSelectedAssistant}
                />
                <TextInput
                  mt="md"
                  label="Phone Number"
                  placeholder="+1555..."
                  value={callPhone}
                  onChange={(e) => setCallPhone(e.currentTarget.value)}
                />
                <Button mt="sm" variant="outline" leftIcon={<IconPhone />} onClick={() => setCallModal(true)}>
                  Preview Call
                </Button>
              </Card>

              <Group position="apart" mt="xl">
                <Button variant="outline" onClick={() => setActiveStep(0)}>Back</Button>
                <Button onClick={handleApproveAndPlan} leftIcon={<IconCheck />}>Approve & Plan</Button>
              </Group>
            </Stack>
          </Box>
        </Stepper.Step>
      </Stepper>

      <Modal opened={callModal} onClose={() => setCallModal(false)} title="Confirm Call">
        <Stack>
          <Text size="sm">Calling {callPhone} via assistant &quot;{selectedAssistant}&quot; with:</Text>
          <Paper p="sm" bg={theme.colorScheme === 'dark' ? 'dark.7' : 'gray.0'}>
            <Text>{generatedBody}</Text>
          </Paper>
          <Group position="right">
            <Button variant="outline" onClick={() => setCallModal(false)}>Cancel</Button>
            <Button onClick={handleApproveAndPlan}>Yes, Call & Plan</Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  );
}
