import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  Container,
  Title,
  Text,
  List,
  Loader,
  Alert,
  Button,
  Paper,
} from "@mantine/core";

export function CampaignDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [plan, setPlan] = useState<{ summary: string; actions: string[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`/api/campaigns/${id}/plan`)
      .then((res) => {
        if (!res.ok) throw new Error(res.statusText);
        return res.json();
      })
      .then((data) => setPlan(data.plan))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Loader />;
  if (error) return <Alert color="red">{error}</Alert>;
  if (!plan) return null;

  return (
    <Container size="sm" py="xl">
      <Paper p="md" withBorder>
        <Title order={2}>Campaign Plan</Title>
        <Text mt="md">{plan.summary}</Text>
        {plan.actions.length > 0 && (
          <List mt="sm" withPadding>
            {plan.actions.map((action, idx) => (
              <List.Item key={idx}>{action}</List.Item>
            ))}
          </List>
        )}
        <Button mt="xl" variant="outline" onClick={() => navigate(-1)}>
          ← Back
        </Button>
      </Paper>
    </Container>
  );
}
