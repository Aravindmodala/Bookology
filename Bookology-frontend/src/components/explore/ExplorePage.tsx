import React, { useMemo, useState } from 'react';
import ExploreHeader from './ExploreHeader';
import FilterChips, { Filters } from './FilterChips';
import HeroCarousel from './HeroCarousel';
import Section from './Section';
import StoryCard, { Story } from './StoryCard';
import { GridSkeleton, HeroSkeleton } from './Skeletons';
import { useQuery } from '@tanstack/react-query';
import { createApiUrl, API_ENDPOINTS } from '../../config';
import { useAuth } from '../../AuthContext';

// Minimal fetchers (wire to real API when available)
async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> { const r = await fetch(url, init); if (!r.ok) throw new Error('Failed'); return r.json(); }

function mapApiToStory(x: any): Story {
  return {
    id: String(x.id),
    title: x.story_title || x.title || 'Untitled',
    subtitle: x.summary || x.story_outline || '',
    coverUrl: x.cover_image_url || x.coverUrl || '',
    genre: x.genre || 'fantasy',
    author: { id: String(x.user_id || ''), name: x.author_name || 'Anonymous' },
    stats: { views: x.views || 0, likes: x.like_count || 0, comments: x.comment_count || 0 },
    isFeatured: Boolean(x.is_featured),
    isPublic: Boolean(x.is_public ?? true),
    createdAt: x.created_at || new Date().toISOString(),
  };
}

function useFeaturedStories() {
  const qs = new URLSearchParams({ page: '1', limit: '5', sort_by: 'published_at' }).toString();
  return useQuery({
    queryKey: ['featured', qs],
    queryFn: async () => {
      const data = await fetchJSON<any>(createApiUrl(`${API_ENDPOINTS.GET_PUBLIC_STORIES}?${qs}`));
      return (data.stories || []).slice(0, 5).map(mapApiToStory);
    },
    staleTime: 5 * 60_000,
  });
}
function useTrendingStories(filters: Filters) {
  const sort_by = 'published_at';
  const params: Record<string, string> = { page: '1', limit: '20', sort_by };
  if (filters.genres && filters.genres[0]) params.genre = filters.genres[0];
  const qs = new URLSearchParams(params).toString();
  return useQuery({
    queryKey: ['trending', qs],
    queryFn: async () => {
      const data = await fetchJSON<any>(createApiUrl(`${API_ENDPOINTS.GET_PUBLIC_STORIES}?${qs}`));
      return (data.stories || []).map(mapApiToStory);
    },
    staleTime: 5 * 60_000,
  });
}
function useNewPublicStories(filters: Filters, page: number) {
  const sort_by = 'created_at';
  const params: Record<string, string> = { page: String(page), limit: '20', sort_by };
  if (filters.genres && filters.genres[0]) params.genre = filters.genres[0];
  const qs = new URLSearchParams(params).toString();
  return useQuery({
    queryKey: ['new', qs],
    queryFn: async () => {
      const data = await fetchJSON<any>(createApiUrl(`${API_ENDPOINTS.GET_PUBLIC_STORIES}?${qs}`));
      return (data.stories || []).map(mapApiToStory);
    },
    staleTime: 5 * 60_000,
  });
}
function useMyPublicStories(userId?: string, page = 1, token?: string) {
  if (!userId || !token) return { data: [] as Story[], isLoading: false } as any;
  return useQuery({
    queryKey: ['mine', userId, page],
    queryFn: async () => {
      const resp = await fetchJSON<any>(createApiUrl('/stories'), {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const stories = (resp.stories || []).filter((s: any) => s.is_public);
      return stories.map(mapApiToStory);
    },
    staleTime: 5 * 60_000,
  });
}

export default function ExplorePage() {
  const [filters, setFilters] = useState<Filters>({ genres: [], sort: 'trending' });
  const [q, setQ] = useState('');
  const { session, user } = useAuth();

  const { data: featured, isLoading: loadingFeatured } = useFeaturedStories();
  const { data: trending, isLoading: loadingTrending } = useTrendingStories({ ...filters, q });
  const { data: fresh, isLoading: loadingFresh } = useNewPublicStories({ ...filters, q }, 1);
  const { data: mine } = useMyPublicStories(user?.id, 1, session?.access_token);

  return (
    <div className="min-h-screen bg-page">
      <ExploreHeader q={q} onQueryChange={setQ} />

      <div className="container py-6 space-y-10">
        {loadingFeatured ? <HeroSkeleton /> : <HeroCarousel stories={featured || []} />}

        <Section title="Trending Now">
          {loadingTrending ? (
            <GridSkeleton count={8} />
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
              {(trending || []).map((s) => (<StoryCard key={s.id} story={s} />))}
            </div>
          )}
        </Section>

        <Section title="New Public Stories" actionSlot={<FilterChips filters={filters} onChange={setFilters} />}>
          {loadingFresh ? (
            <GridSkeleton count={12} />
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
              {(fresh || []).map((s) => (<StoryCard key={s.id} story={s} />))}
            </div>
          )}
        </Section>

        {!!(mine && mine.length) && (
          <Section title="My Public Stories">
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
              {mine!.map((s) => (<StoryCard key={s.id} story={s} highlightGold />))}
            </div>
          </Section>
        )}
      </div>
    </div>
  );
}


