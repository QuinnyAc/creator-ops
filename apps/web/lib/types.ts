export type DashboardSummary = {
  inspirations_inbox: number;
  topics_approved: number;
  contents_in_progress: number;
  publications_scheduled: number;
  contents_to_review: number;
};

export type AnalyticsSummary = {
  publications: number;
  views: number;
  likes: number;
  comments: number;
  favorites: number;
  shares: number;
  followers_gained: number;
  engagement_rate: number;
};

export type PillarAnalyticsItem = {
  pillar_id: string;
  pillar_name: string;
  publications: number;
  views: number;
  likes: number;
  comments: number;
  favorites: number;
  shares: number;
  followers_gained: number;
  avg_views: number;
  engagement_rate: number;
  favorite_rate: number;
  follower_conversion_rate: number;
};

export type Inspiration = {
  id: string;
  user_id: string;
  title: string;
  note: string | null;
  source: string | null;
  source_url: string | null;
  status: string;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
};

export type ContentPillar = {
  id: string;
  user_id: string;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type Tag = {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
  updated_at: string;
};

export type Topic = {
  id: string;
  user_id: string;
  inspiration_id: string | null;
  pillar_id: string | null;
  title: string;
  core_idea: string | null;
  target_audience: string | null;
  user_problem: string | null;
  angle: string | null;
  goal: string | null;
  status: string;
  planned_platforms: string[];
  opportunity_score?: number | string | null;
  priority_score?: number | string | null;
  created_at: string;
  updated_at: string;
};

export type TopicScore = {
  id: string;
  topic_id: string;
  pain_point: number;
  search_demand: number;
  trend_heat: number;
  differentiation: number;
  commercial_value: number;
  production_effort: number;
  opportunity_score: number | string;
  priority_score: number | string;
  created_at: string;
  updated_at: string;
};

export type ContentItem = {
  id: string;
  user_id: string;
  topic_id: string | null;
  pillar_id: string | null;
  title: string;
  content_type: string;
  status: string;
  research_notes: string | null;
  outline: string | null;
  script: string | null;
  copywriting: string | null;
  cta: string | null;
  planned_publish_at: string | null;
  created_at: string;
  updated_at: string;
};

export type Platform = {
  id: string;
  slug: string;
  name: string;
};

export type PlatformAccount = {
  id: string;
  user_id: string;
  platform_id: string;
  name: string;
  handle: string | null;
  created_at: string;
  updated_at: string;
};

export type Publication = {
  id: string;
  content_id: string;
  platform_account_id: string;
  title: string | null;
  copywriting: string | null;
  cover_url: string | null;
  platform_tags: string[];
  status: string;
  scheduled_at: string | null;
  published_at: string | null;
  url: string | null;
  created_at: string;
  updated_at: string;
};

export type MetricSnapshot = {
  id: string;
  publication_id: string;
  captured_at: string;
  views: number;
  likes: number;
  comments: number;
  favorites: number;
  shares: number;
  followers_gained: number;
  extra_metrics: Record<string, number | string>;
};

export type Review = {
  id: string;
  content_id: string;
  goal: string | null;
  expected_outcome: string | null;
  what_worked: string | null;
  what_didnt_work: string | null;
  learnings: string | null;
  next_action: string | null;
  created_at: string;
  updated_at: string;
};
