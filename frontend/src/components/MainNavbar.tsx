import React, { useState } from 'react';
import { createStyles, Navbar, Group, Text, ThemeIcon, UnstyledButton, rem } from '@mantine/core';
import {
  IconDashboard,
  IconBrandCampaignmonitor,
  IconFileText,
  IconRobot,
  IconWorld,
  IconChartBar,
  IconSettings,
  IconUsers,
  IconCalendarEvent,
  IconBrandGmail,
} from '@tabler/icons-react';
import { useLocation, useNavigate } from 'react-router-dom';

// Define styles for the navbar
const useStyles = createStyles((theme) => ({
  navbar: {
    paddingTop: 0,
  },

  section: {
    marginBottom: theme.spacing.md,
  },

  mainLinks: {
    paddingLeft: theme.spacing.md - rem(6),
    paddingRight: theme.spacing.md - rem(6),
    paddingBottom: theme.spacing.md,
  },

  mainLink: {
    display: 'flex',
    alignItems: 'center',
    width: '100%',
    fontSize: theme.fontSizes.xs,
    padding: `${rem(8)} ${theme.spacing.xs}`,
    borderRadius: theme.radius.sm,
    fontWeight: 500,
    color: theme.colorScheme === 'dark' ? theme.colors.dark[0] : theme.colors.gray[7],

    '&:hover': {
      backgroundColor: theme.colorScheme === 'dark' ? theme.colors.dark[6] : theme.colors.gray[0],
      color: theme.colorScheme === 'dark' ? theme.white : theme.black,
    },
  },

  mainLinkActive: {
    '&, &:hover': {
      backgroundColor: theme.fn.variant({ variant: 'light', color: theme.primaryColor }).background,
      color: theme.fn.variant({ variant: 'light', color: theme.primaryColor }).color,
    },
  },

  mainLinkInner: {
    display: 'flex',
    alignItems: 'center',
    flex: 1,
  },

  mainLinkIcon: {
    marginRight: theme.spacing.sm,
    color: theme.colorScheme === 'dark' ? theme.colors.dark[2] : theme.colors.gray[6],
  },

  mainLinkIconActive: {
    color: theme.fn.variant({ variant: 'light', color: theme.primaryColor }).color,
  },

  title: {
    textTransform: 'uppercase',
    letterSpacing: rem(-0.25),
    fontWeight: 700,
    fontSize: theme.fontSizes.xs,
    color: theme.colorScheme === 'dark' ? theme.colors.dark[2] : theme.colors.gray[6],
    marginBottom: theme.spacing.xs,
    paddingLeft: theme.spacing.md,
    paddingTop: theme.spacing.md,
    borderTop: `${rem(1)} solid ${
      theme.colorScheme === 'dark' ? theme.colors.dark[4] : theme.colors.gray[2]
    }`,
  },
}));

// Define the main navigation links
const mainNavLinks = [
  { icon: IconDashboard, label: 'Dashboard', path: '/' },
  { icon: IconBrandCampaignmonitor, label: 'Campaigns', path: '/campaigns' },
  { icon: IconFileText, label: 'Content', path: '/content' },
  { icon: IconRobot, label: 'Agents', path: '/agents' },
  { icon: IconWorld, label: 'Localization', path: '/localization' },
  { icon: IconChartBar, label: 'Analytics', path: '/analytics' },
];

// Define the secondary navigation links
const toolsLinks = [
  { icon: IconCalendarEvent, label: 'Scheduler', path: '/scheduler' },
  { icon: IconUsers, label: 'Audience', path: '/audience' },
  { icon: IconBrandGmail, label: 'Email Outreach', path: '/email-outreach' },
  { icon: IconSettings, label: 'Settings', path: '/settings' },
];

export function MainNavbar() {
  const { classes, cx } = useStyles();
  const location = useLocation();
  const navigate = useNavigate();

  // Function to check if a link is active
  const isLinkActive = (path: string) => {
    if (path === '/' && location.pathname === '/') {
      return true;
    }
    if (path !== '/' && location.pathname.startsWith(path)) {
      return true;
    }
    return false;
  };

  // Render main links
  const mainLinks = mainNavLinks.map((link) => (
    <UnstyledButton
      key={link.label}
      className={cx(classes.mainLink, { [classes.mainLinkActive]: isLinkActive(link.path) })}
      onClick={() => navigate(link.path)}
    >
      <div className={classes.mainLinkInner}>
        <link.icon
          size={20}
          className={cx(classes.mainLinkIcon, { [classes.mainLinkIconActive]: isLinkActive(link.path) })}
          stroke={1.5}
        />
        <span>{link.label}</span>
      </div>
    </UnstyledButton>
  ));

  // Render tools links
  const tools = toolsLinks.map((link) => (
    <UnstyledButton
      key={link.label}
      className={cx(classes.mainLink, { [classes.mainLinkActive]: isLinkActive(link.path) })}
      onClick={() => navigate(link.path)}
    >
      <div className={classes.mainLinkInner}>
        <link.icon
          size={20}
          className={cx(classes.mainLinkIcon, { [classes.mainLinkIconActive]: isLinkActive(link.path) })}
          stroke={1.5}
        />
        <span>{link.label}</span>
      </div>
    </UnstyledButton>
  ));

  return (
    <Navbar.Section grow className={classes.navbar}>
      <div className={classes.mainLinks}>{mainLinks}</div>
      <Text className={classes.title}>Tools</Text>
      <div className={classes.mainLinks}>{tools}</div>
    </Navbar.Section>
  );
}
