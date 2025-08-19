import React, { useRef, useState } from 'react';
import ExploreHeader from './ExploreHeader';
import HeroCarousel from './HeroCarousel';
import StoryCard, { Story } from './StoryCard';
import { GridSkeleton, HeroSkeleton } from './Skeletons';
import { useQuery } from '@tanstack/react-query';
import { createApiUrl, API_ENDPOINTS } from '../../config';
import { useAuth } from '../../AuthContext';
import { MotionConfig } from 'framer-motion';

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
		aspectRatio: typeof x.cover_aspect_ratio === 'number' && x.cover_aspect_ratio > 0
			? x.cover_aspect_ratio
			: (x.cover_image_width && x.cover_image_height && x.cover_image_height > 0
				? x.cover_image_width / x.cover_image_height
				: 2/3),
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

function useTrendingStories() {
	const qs = new URLSearchParams({ page: '1', limit: '20', sort_by: 'published_at' }).toString();
	return useQuery({
		queryKey: ['trending', qs],
		queryFn: async () => {
			const data = await fetchJSON<any>(createApiUrl(`${API_ENDPOINTS.GET_PUBLIC_STORIES}?${qs}`));
			return (data.stories || []).map(mapApiToStory);
		},
		staleTime: 5 * 60_000,
	});
}

function useNewPublicStories(page: number) {
	const qs = new URLSearchParams({ page: String(page), limit: '20', sort_by: 'created_at' }).toString();
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

function Row({ title, items, loading }: { title: string; items: Story[]; loading?: boolean }) {
	const ref = useRef<HTMLDivElement>(null);
	function scroll(dir: number) {
		const el = ref.current;
		if (!el) return;
		const amount = Math.max(300, Math.floor(el.clientWidth * 0.85)) * dir;
		el.scrollBy({ left: amount, behavior: 'smooth' });
	}
	return (
		<div className="relative">
			<div className="mb-3 px-1 flex items-center justify-between">
				<h2 className="text-xl md:text-2xl font-display font-semibold tracking-tight text-white whitespace-nowrap">{title}</h2>
				<div className="hidden md:flex gap-2">
					<button onClick={() => scroll(-1)} className="h-10 w-10 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors">◀</button>
					<button onClick={() => scroll(1)} className="h-10 w-10 rounded-full bg-white/10 hover:bg-white/20 text-white transition-colors">▶</button>
				</div>
			</div>
			{loading ? (
				<GridSkeleton count={12} />
			) : (
				<div className="relative">
					<div className="pointer-events-none absolute left-0 top-0 h-full w-10 bg-gradient-to-r from-black to-transparent" />
					<div className="pointer-events-none absolute right-0 top-0 h-full w-10 bg-gradient-to-l from-black to-transparent" />
					<div
						ref={ref}
						className="flex gap-4 overflow-x-auto scroll-smooth snap-x snap-mandatory pb-2 transform-gpu"
						style={{ scrollbarWidth: 'none', overscrollBehaviorX: 'contain', WebkitOverflowScrolling: 'touch' }}
					>
						{items.map((s) => (
							<div key={s.id} className="snap-start shrink-0 w-[220px] md:w-[280px]">
								<StoryCard story={s} />
							</div>
						))}
					</div>
				</div>
			)}
		</div>
	);
}

export default function ExplorePage() {
	const [q, setQ] = useState('');
	const { session, user } = useAuth();

	const { data: featured, isLoading: loadingFeatured } = useFeaturedStories();
	const { data: trending, isLoading: loadingTrending } = useTrendingStories();
	const { data: fresh, isLoading: loadingFresh } = useNewPublicStories(1);
	const { data: mine } = useMyPublicStories(user?.id, 1, session?.access_token);

	return (
		<MotionConfig reducedMotion="user" transition={{ type: 'spring', stiffness: 260, damping: 24, mass: 0.9 }}>
			<div className="min-h-screen bg-black">
				<ExploreHeader q={q} onQueryChange={setQ} />
				<div className="container py-6 space-y-10">
					{loadingFeatured ? <HeroSkeleton /> : <HeroCarousel stories={featured || []} />}
					<Row title="Trending Now" items={trending || []} loading={loadingTrending} />
					<Row title="New Releases" items={fresh || []} loading={loadingFresh} />
					{!!(mine && mine.length) && <Row title="My Public Stories" items={mine || []} />}
				</div>
			</div>
		</MotionConfig>
	);
}
