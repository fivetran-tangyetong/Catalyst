import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Card,
  Container,
  Divider,
  Grid,
  Group,
  Image,
  LoadingOverlay,
  Paper,
  Radio,
  Select,
  Stack,
  Stepper,
  Text,
  Textarea,
  TextInput,
  Title,
  useMantineTheme,
  MultiSelect,
  ColorInput,
  SegmentedControl,
  Tabs,
  Badge,
  ActionIcon,
  Tooltip,
  Alert,
  ScrollArea,
  Switch,
  Accordion,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { 
  IconFileText, 
  IconPhoto, 
  IconLayoutGrid, 
  IconBrandCampaignmonitor,
  IconCheck,
  IconAlertCircle,
  IconRefresh,
  IconArrowRight,
  IconDeviceFloppy,
  IconWorld,
  IconPalette,
  IconBrandFacebook,
  IconBrandInstagram,
  IconBrandTwitter,
  IconBrandLinkedin,
  IconMail,
  IconInfoCircle,
  IconUpload,
  IconTrash,
  IconEdit,
} from '@tabler/icons-react';
import { Dropzone, FileWithPath, IMAGE_MIME_TYPE } from '@mantine/dropzone';
import { useNavigate } from 'react-router-dom';

// Types
interface ContentGenerationFormValues {
  contentType: string;
  title: string;
  description: string;
  platform: string;
  targetAudience: string;
  productInfo: {
    name: string;
    feature: string;
    benefit: string;
    painPoint: string;
    companyName: string;
    companyContact: string;
  };
  textParams: {
    tone: string;
    templateId: string;
    keywords: string[];
    characterLimit: number | null;
  };
  visualParams: {
    style: string;
    aspectRatio: string;
    colors: string[];
    useSketch: boolean;
  };
  targetLanguages: string[];
}

interface ContentTemplate {
  id: string;
  name: string;
  description: string;
  type: string;
}

interface GeneratedContent {
  contentId: string;
  contentType: string;
  textContent?: {
    title: string;
    body: string;
    cta: string;
  };
  visualContent?: {
    title: string;
    imageUrl: string;
    imageBase64: string;
  };
  preview?: {
    title: string;
    platform: string;
    textPreview: string;
    hasImage: boolean;
    cta: string;
  };
}

// Mock data
const contentTypes = [
  { value: 'social_post', label: 'Social Media Post', icon: IconBrandFacebook },
  { value: 'email', label: 'Email', icon: IconMail },
  { value: 'ad', label: 'Advertisement', icon: IconLayoutGrid },
  { value: 'banner', label: 'Banner', icon: IconPhoto },
  { value: 'product_image', label: 'Product Image', icon: IconPhoto },
  { value: 'blog_post', label: 'Blog Post', icon: IconFileText },
];

const platforms = [
  { value: 'facebook', label: 'Facebook', icon: IconBrandFacebook },
  { value: 'instagram', label: 'Instagram', icon: IconBrandInstagram },
  { value: 'twitter', label: 'Twitter', icon: IconBrandTwitter },
  { value: 'linkedin', label: 'LinkedIn', icon: IconBrandLinkedin },
  { value: 'email', label: 'Email', icon: IconMail },
  { value: 'website', label: 'Website', icon: IconWorld },
];

const toneOptions = [
  { value: 'professional', label: 'Professional' },
  { value: 'casual', label: 'Casual' },
  { value: 'friendly', label: 'Friendly' },
  { value: 'enthusiastic', label: 'Enthusiastic' },
  { value: 'formal', label: 'Formal' },
  { value: 'humorous', label: 'Humorous' },
];

const styleOptions = [
  { value: 'realistic', label: 'Realistic' },
  { value: 'artistic', label: 'Artistic' },
  { value: 'minimalist', label: 'Minimalist' },
  { value: 'vibrant', label: 'Vibrant' },
  { value: 'vintage', label: 'Vintage' },
  { value: 'corporate', label: 'Corporate' },
];

const aspectRatioOptions = [
  { value: '1:1', label: 'Square (1:1)' },
  { value: '4:3', label: 'Standard (4:3)' },
  { value: '16:9', label: 'Widescreen (16:9)' },
  { value: '9:16', label: 'Portrait (9:16)' },
  { value: '3:2', label: 'Classic (3:2)' },
];

const mockTemplates: ContentTemplate[] = [
  { id: 'social_basic_1', name: 'Basic Social Media Post', description: 'A simple social media post with a hook, body, and call to action', type: 'social_post' },
  { id: 'email_announcement_1', name: 'Product Announcement Email', description: 'An email template for announcing a new product or feature', type: 'email' },
  { id: 'ad_copy_1', name: 'Basic Ad Copy', description: 'A template for creating ad copy with headline, body, and CTA', type: 'ad_copy' },
];

const languageOptions = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'it', label: 'Italian' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'ja', label: 'Japanese' },
  { value: 'zh', label: 'Chinese' },
];

// Component
export function ContentCreator() {
  const theme = useMantineTheme();
  const navigate = useNavigate();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [generatedContent, setGeneratedContent] = useState<GeneratedContent | null>(null);
  const [sketchFile, setSketchFile] = useState<FileWithPath | null>(null);
  const [sketchPreview, setSketchPreview] = useState<string | null>(null);
  const [contentTypeCategory, setContentTypeCategory] = useState<'text' | 'visual' | 'combined'>('combined');

  // Initialize form with default values
  const form = useForm<ContentGenerationFormValues>({
    initialValues: {
      contentType: 'social_post',
      title: '',
      description: '',
      platform: 'facebook',
      targetAudience: '',
      productInfo: {
        name: '',
        feature: '',
        benefit: '',
        painPoint: '',
        companyName: '',
        companyContact: '',
      },
      textParams: {
        tone: 'professional',
        templateId: '',
        keywords: [],
        characterLimit: null,
      },
      visualParams: {
        style: 'realistic',
        aspectRatio: '1:1',
        colors: [],
        useSketch: false,
      },
      targetLanguages: [],
    },
    validate: {
      contentType: (value) => (value ? null : 'Content type is required'),
      title: (value) => (value ? null : 'Title is required'),
      productInfo: {
        name: (value) => (value ? null : 'Product name is required'),
      },
    },
  });

  // Update content type category when content type changes
  useEffect(() => {
    const contentType = form.values.contentType;
    if (['banner', 'product_image'].includes(contentType)) {
      setContentTypeCategory('visual');
    } else if (['blog_post'].includes(contentType)) {
      setContentTypeCategory('text');
    } else {
      setContentTypeCategory('combined');
    }
  }, [form.values.contentType]);

  // Handle file upload for sketch
  const handleSketchDrop = (files: FileWithPath[]) => {
    if (files.length > 0) {
      setSketchFile(files[0]);
      const reader = new FileReader();
      reader.onload = (e) => {
        if (e.target?.result) {
          setSketchPreview(e.target.result as string);
          form.setFieldValue('visualParams.useSketch', true);
        }
      };
      reader.readAsDataURL(files[0]);
    }
  };

  // Clear sketch file
  const clearSketch = () => {
    setSketchFile(null);
    setSketchPreview(null);
    form.setFieldValue('visualParams.useSketch', false);
  };

  // Filter templates based on content type
  const filteredTemplates = mockTemplates.filter(
    (template) => template.type === form.values.contentType || 
                  (template.type === 'ad_copy' && form.values.contentType === 'ad')
  );

  // Handle form submission
  const handleSubmit = async () => {
    if (activeStep === 0) {
      // Validate first step
      const errors = form.validate();
      if (errors.hasErrors) {
        return;
      }
      setActiveStep(1);
      return;
    }

    if (activeStep === 1) {
      // Start content generation
      setLoading(true);
      setError(null);

      try {
        // In a real implementation, this would be an API call
        // const response = await fetch('/api/content', {
        //   method: 'POST',
        //   headers: { 'Content-Type': 'application/json' },
        //   body: JSON.stringify({
        //     contentType: form.values.contentType,
        //     title: form.values.title,
        //     description: form.values.description,
        //     parameters: {
        //       platform: form.values.platform,
        //       targetAudience: form.values.targetAudience,
        //       productInfo: form.values.productInfo,
        //       textParams: form.values.textParams,
        //       visualParams: form.values.visualParams,
        //     },
        //     targetLanguages: form.values.targetLanguages,
        //   }),
        // });
        // const data = await response.json();

        // Simulate API call with a delay
        await new Promise((resolve) => setTimeout(resolve, 2000));

        // Mock response data
        const mockResponse: GeneratedContent = {
          contentId: `content_${Date.now()}`,
          contentType: form.values.contentType,
          textContent: contentTypeCategory !== 'visual' ? {
            title: form.values.title,
            body: `🔥 Introducing ${form.values.productInfo.name}!\n\nOur ${form.values.productInfo.name} helps you ${form.values.productInfo.benefit} with its innovative ${form.values.productInfo.feature}. Say goodbye to ${form.values.productInfo.painPoint} and hello to a better experience.\n\nClick the link to learn more and get 10% off your first purchase!`,
            cta: 'Shop Now',
          } : undefined,
          visualContent: contentTypeCategory !== 'text' ? {
            title: form.values.title,
            imageUrl: 'https://placehold.co/600x600/4672b4/white?text=AI+Generated+Image',
            imageBase64: '',
          } : undefined,
          preview: contentTypeCategory === 'combined' ? {
            title: form.values.title,
            platform: form.values.platform,
            textPreview: `🔥 Introducing ${form.values.productInfo.name}! Our ${form.values.productInfo.name} helps you ${form.values.productInfo.benefit}...`,
            hasImage: true,
            cta: 'Shop Now',
          } : undefined,
        };

        setGeneratedContent(mockResponse);
        setActiveStep(2);
        notifications.show({
          title: 'Content Generated',
          message: 'Your content has been successfully generated',
          color: 'green',
          icon: <IconCheck size={16} />,
        });
      } catch (err) {
        console.error('Error generating content:', err);
        setError('Failed to generate content. Please try again.');
        notifications.show({
          title: 'Error',
          message: 'Failed to generate content. Please try again.',
          color: 'red',
          icon: <IconAlertCircle size={16} />,
        });
      } finally {
        setLoading(false);
      }
    }
  };

  // Handle content approval
  const handleApproveContent = () => {
    notifications.show({
      title: 'Content Approved',
      message: 'Your content has been approved and saved',
      color: 'green',
      icon: <IconCheck size={16} />,
    });
    navigate('/content');
  };

  // Handle content regeneration
  const handleRegenerateContent = () => {
    setActiveStep(1);
    setGeneratedContent(null);
    handleSubmit();
  };

  // Render content preview based on type
  const renderContentPreview = () => {
    if (!generatedContent) return null;

    if (contentTypeCategory === 'text') {
      return (
        <Paper p="md" withBorder>
          <Title order={4}>{generatedContent.textContent?.title}</Title>
          <Text style={{ whiteSpace: 'pre-line' }} my="md">
            {generatedContent.textContent?.body}
          </Text>
          <Button variant="light">{generatedContent.textContent?.cta}</Button>
        </Paper>
      );
    }

    if (contentTypeCategory === 'visual') {
      return (
        <Paper p="md" withBorder>
          <Title order={5} mb="xs">{generatedContent.visualContent?.title}</Title>
          <Image
            src={generatedContent.visualContent?.imageUrl}
            alt={generatedContent.visualContent?.title}
            radius="md"
          />
        </Paper>
      );
    }

    // Combined content
    return (
      <Paper p="md" withBorder>
        <Group position="apart" mb="xs">
          <Title order={4}>{generatedContent.preview?.title}</Title>
          <Badge color="blue">{generatedContent.preview?.platform}</Badge>
        </Group>
        
        <Grid>
          <Grid.Col span={6}>
            <Image
              src={generatedContent.visualContent?.imageUrl}
              alt={generatedContent.visualContent?.title}
              radius="md"
            />
          </Grid.Col>
          <Grid.Col span={6}>
            <Text style={{ whiteSpace: 'pre-line' }}>
              {generatedContent.textContent?.body}
            </Text>
            <Button variant="light" mt="md">{generatedContent.textContent?.cta}</Button>
          </Grid.Col>
        </Grid>
      </Paper>
    );
  };

  return (
    <Container size="xl" py="xl">
      <Paper p="md" withBorder mb="xl">
        <Title order={2} mb="md">Create New Content</Title>
        <Stepper active={activeStep} onStepClick={setActiveStep} breakpoint="sm">
          <Stepper.Step
            label="Content Details"
            description="Define your content"
            icon={<IconFileText size={18} />}
          >
            <Box mt="xl">
              <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
                <Stack spacing="lg">
                  <Select
                    label="Content Type"
                    placeholder="Select content type"
                    data={contentTypes.map(type => ({ value: type.value, label: type.label }))}
                    icon={<IconLayoutGrid size={16} />}
                    required
                    {...form.getInputProps('contentType')}
                  />

                  <TextInput
                    label="Title"
                    placeholder="Enter a title for your content"
                    required
                    {...form.getInputProps('title')}
                  />

                  <Textarea
                    label="Description"
                    placeholder="Describe what you want to create"
                    minRows={3}
                    {...form.getInputProps('description')}
                  />

                  <Select
                    label="Platform"
                    placeholder="Select platform"
                    data={platforms.map(platform => ({ value: platform.value, label: platform.label }))}
                    icon={<IconWorld size={16} />}
                    {...form.getInputProps('platform')}
                  />

                  <TextInput
                    label="Target Audience"
                    placeholder="Who is this content for? (e.g., 'Fitness enthusiasts aged 25-45')"
                    {...form.getInputProps('targetAudience')}
                  />

                  <Divider label="Product Information" labelPosition="center" />

                  <Grid>
                    <Grid.Col xs={12} md={6}>
                      <TextInput
                        label="Product Name"
                        placeholder="Enter product name"
                        required
                        {...form.getInputProps('productInfo.name')}
                      />
                    </Grid.Col>
                    <Grid.Col xs={12} md={6}>
                      <TextInput
                        label="Key Feature"
                        placeholder="Enter a key feature"
                        {...form.getInputProps('productInfo.feature')}
                      />
                    </Grid.Col>
                    <Grid.Col xs={12} md={6}>
                      <TextInput
                        label="Main Benefit"
                        placeholder="What benefit does it provide?"
                        {...form.getInputProps('productInfo.benefit')}
                      />
                    </Grid.Col>
                    <Grid.Col xs={12} md={6}>
                      <TextInput
                        label="Pain Point Solved"
                        placeholder="What problem does it solve?"
                        {...form.getInputProps('productInfo.painPoint')}
                      />
                    </Grid.Col>
                    <Grid.Col xs={12} md={6}>
                      <TextInput
                        label="Company Name"
                        placeholder="Your company name"
                        {...form.getInputProps('productInfo.companyName')}
                      />
                    </Grid.Col>
                    <Grid.Col xs={12} md={6}>
                      <TextInput
                        label="Company Contact"
                        placeholder="Contact person name"
                        {...form.getInputProps('productInfo.companyContact')}
                      />
                    </Grid.Col>
                  </Grid>

                  <Group position="right" mt="xl">
                    <Button 
                      type="submit" 
                      rightIcon={<IconArrowRight size={16} />}
                    >
                      Next Step
                    </Button>
                  </Group>
                </Stack>
              </form>
            </Box>
          </Stepper.Step>

          <Stepper.Step
            label="Content Parameters"
            description="Set generation options"
            icon={<IconPalette size={18} />}
          >
            <Box mt="xl">
              <form onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
                <Stack spacing="lg">
                  <Tabs defaultValue="text">
                    <Tabs.List>
                      {contentTypeCategory !== 'visual' && (
                        <Tabs.Tab value="text" icon={<IconFileText size={14} />}>Text Options</Tabs.Tab>
                      )}
                      {contentTypeCategory !== 'text' && (
                        <Tabs.Tab value="visual" icon={<IconPhoto size={14} />}>Visual Options</Tabs.Tab>
                      )}
                      <Tabs.Tab value="localization" icon={<IconWorld size={14} />}>Localization</Tabs.Tab>
                    </Tabs.List>

                    {contentTypeCategory !== 'visual' && (
                      <Tabs.Panel value="text" pt="xs">
                        <Stack spacing="md" mt="md">
                          <Select
                            label="Tone"
                            placeholder="Select content tone"
                            data={toneOptions}
                            {...form.getInputProps('textParams.tone')}
                          />

                          {filteredTemplates.length > 0 && (
                            <Select
                              label="Template"
                              placeholder="Select a template (optional)"
                              data={filteredTemplates.map(template => ({ 
                                value: template.id, 
                                label: template.name,
                                description: template.description
                              }))}
                              {...form.getInputProps('textParams.templateId')}
                            />
                          )}

                          <MultiSelect
                            label="Keywords"
                            placeholder="Enter keywords (press Enter after each)"
                            data={form.values.textParams.keywords}
                            searchable
                            creatable
                            getCreateLabel={(query) => `+ Add ${query}`}
                            onCreate={(query) => {
                              const keywords = [...form.values.textParams.keywords, query];
                              form.setFieldValue('textParams.keywords', keywords);
                              return query;
                            }}
                            {...form.getInputProps('textParams.keywords')}
                          />

                          <TextInput
                            label="Character Limit"
                            placeholder="Maximum characters (optional)"
                            type="number"
                            {...form.getInputProps('textParams.characterLimit')}
                          />
                        </Stack>
                      </Tabs.Panel>
                    )}

                    {contentTypeCategory !== 'text' && (
                      <Tabs.Panel value="visual" pt="xs">
                        <Stack spacing="md" mt="md">
                          <Select
                            label="Visual Style"
                            placeholder="Select visual style"
                            data={styleOptions}
                            {...form.getInputProps('visualParams.style')}
                          />

                          <Select
                            label="Aspect Ratio"
                            placeholder="Select aspect ratio"
                            data={aspectRatioOptions}
                            {...form.getInputProps('visualParams.aspectRatio')}
                          />

                          <Box>
                            <Text size="sm" weight={500} mb={5}>
                              Color Palette
                            </Text>
                            <Group spacing="xs" mb="xs">
                              {form.values.visualParams.colors.map((color, index) => (
                                <ColorInput
                                  key={index}
                                  value={color}
                                  onChange={(value) => {
                                    const colors = [...form.values.visualParams.colors];
                                    colors[index] = value;
                                    form.setFieldValue('visualParams.colors', colors);
                                  }}
                                  format="hex"
                                  swatches={['#25262b', '#868e96', '#fa5252', '#e64980', '#be4bdb', '#7950f2', '#4c6ef5', '#228be6', '#15aabf', '#12b886', '#40c057', '#82c91e', '#fab005', '#fd7e14']}
                                  size="xs"
                                  style={{ width: 100 }}
                                  rightSection={
                                    <ActionIcon
                                      size="xs"
                                      onClick={() => {
                                        const colors = form.values.visualParams.colors.filter((_, i) => i !== index);
                                        form.setFieldValue('visualParams.colors', colors);
                                      }}
                                    >
                                      <IconTrash size={12} />
                                    </ActionIcon>
                                  }
                                />
                              ))}
                              {form.values.visualParams.colors.length < 5 && (
                                <Button
                                  variant="outline"
                                  size="xs"
                                  onClick={() => {
                                    const colors = [...form.values.visualParams.colors, '#228be6'];
                                    form.setFieldValue('visualParams.colors', colors);
                                  }}
                                >
                                  Add Color
                                </Button>
                              )}
                            </Group>
                          </Box>

                          <Divider label="Use Sketch" labelPosition="center" />

                          <Switch
                            label="Generate from sketch"
                            checked={form.values.visualParams.useSketch}
                            onChange={(event) => {
                              form.setFieldValue('visualParams.useSketch', event.currentTarget.checked);
                              if (!event.currentTarget.checked) {
                                clearSketch();
                              }
                            }}
                          />

                          {form.values.visualParams.useSketch && (
                            <Box>
                              {sketchPreview ? (
                                <Box pos="relative">
                                  <Image
                                    src={sketchPreview}
                                    alt="Sketch preview"
                                    radius="md"
                                    height={200}
                                    fit="contain"
                                  />
                                  <Group position="center" mt="xs">
                                    <Button size="xs" variant="light" color="red" onClick={clearSketch}>
                                      Remove Sketch
                                    </Button>
                                  </Group>
                                </Box>
                              ) : (
                                <Dropzone
                                  onDrop={handleSketchDrop}
                                  accept={IMAGE_MIME_TYPE}
                                  maxSize={5 * 1024 * 1024}
                                >
                                  <Group position="center" spacing="xl" style={{ minHeight: 120, pointerEvents: 'none' }}>
                                    <Dropzone.Accept>
                                      <IconUpload size={50} stroke={1.5} color={theme.colors[theme.primaryColor][6]} />
                                    </Dropzone.Accept>
                                    <Dropzone.Reject>
                                      <IconX size={50} stroke={1.5} color={theme.colors.red[6]} />
                                    </Dropzone.Reject>
                                    <Dropzone.Idle>
                                      <IconPhoto size={50} stroke={1.5} />
                                    </Dropzone.Idle>

                                    <div>
                                      <Text size="xl" inline>
                                        Drag sketch here or click to select
                                      </Text>
                                      <Text size="sm" color="dimmed" inline mt={7}>
                                        Upload a hand-drawn sketch to transform into a professional image
                                      </Text>
                                    </div>
                                  </Group>
                                </Dropzone>
                              )}
                            </Box>
                          )}
                        </Stack>
                      </Tabs.Panel>
                    )}

                    <Tabs.Panel value="localization" pt="xs">
                      <Stack spacing="md" mt="md">
                        <MultiSelect
                          label="Target Languages"
                          placeholder="Select languages for localization"
                          data={languageOptions}
                          searchable
                          {...form.getInputProps('targetLanguages')}
                        />

                        <Alert icon={<IconInfoCircle size={16} />} color="blue">
                          Content will be automatically translated to the selected languages using DeepL translation services.
                        </Alert>
                      </Stack>
                    </Tabs.Panel>
                  </Tabs>

                  <Group position="apart" mt="xl">
                    <Button variant="light" onClick={() => setActiveStep(0)}>
                      Back
                    </Button>
                    <Button 
                      type="submit" 
                      loading={loading}
                    >
                      Generate Content
                    </Button>
                  </Group>
                </Stack>
              </form>
            </Box>
          </Stepper.Step>

          <Stepper.Step
            label="Review & Approve"
            description="Finalize content"
            icon={<IconCheck size={18} />}
          >
            <Box mt="xl">
              <LoadingOverlay visible={loading} overlayBlur={2} />
              
              {error && (
                <Alert color="red" title="Error" mb="md">
                  {error}
                </Alert>
              )}

              {generatedContent && (
                <Stack spacing="lg">
                  <Title order={3}>Generated Content</Title>
                  
                  {renderContentPreview()}

                  <Accordion>
                    <Accordion.Item value="details">
                      <Accordion.Control>Content Details</Accordion.Control>
                      <Accordion.Panel>
                        <ScrollArea style={{ height: 200 }}>
                          <Stack spacing="xs">
                            <Group>
                              <Text weight={600}>Content ID:</Text>
                              <Text>{generatedContent.contentId}</Text>
                            </Group>
                            <Group>
                              <Text weight={600}>Content Type:</Text>
                              <Text>{generatedContent.contentType}</Text>
                            </Group>
                            <Group>
                              <Text weight={600}>Platform:</Text>
                              <Text>{form.values.platform}</Text>
                            </Group>
                            <Group>
                              <Text weight={600}>Target Audience:</Text>
                              <Text>{form.values.targetAudience || 'Not specified'}</Text>
                            </Group>
                            {form.values.targetLanguages.length > 0 && (
                              <Group>
                                <Text weight={600}>Localization:</Text>
                                <Group spacing="xs">
                                  {form.values.targetLanguages.map((lang) => (
                                    <Badge key={lang}>
                                      {languageOptions.find(l => l.value === lang)?.label || lang}
                                    </Badge>
                                  ))}
                                </Group>
                              </Group>
                            )}
                          </Stack>
                        </ScrollArea>
                      </Accordion.Panel>
                    </Accordion.Item>
                  </Accordion>

                  <Group position="apart" mt="xl">
                    <Group>
                      <Button 
                        variant="light" 
                        leftIcon={<IconEdit size={16} />}
                        onClick={() => setActiveStep(0)}
                      >
                        Edit Details
                      </Button>
                      <Button 
                        variant="light" 
                        color="blue" 
                        leftIcon={<IconRefresh size={16} />}
                        onClick={handleRegenerateContent}
                      >
                        Regenerate
                      </Button>
                    </Group>
                    <Button 
                      color="green" 
                      leftIcon={<IconCheck size={16} />}
                      onClick={handleApproveContent}
                    >
                      Approve & Save
                    </Button>
                  </Group>
                </Stack>
              )}
            </Box>
          </Stepper.Step>
        </Stepper>
      </Paper>
    </Container>
  );
}
