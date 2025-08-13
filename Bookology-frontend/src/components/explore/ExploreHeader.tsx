import React from 'react';
import { Search, SlidersHorizontal } from 'lucide-react';

type ExploreHeaderProps = {
	title?: string;
	subtitle?: string;
	q: string;
	onQueryChange: (q: string) => void;
	toolbar?: React.ReactNode;
};

export default function ExploreHeader({
	title = 'Explore Stories',
	subtitle = 'Discover captivating stories',
	q,
	onQueryChange,
	toolbar,
}: ExploreHeaderProps) {
	return (
		<div className="sticky top-0 z-30 glass">
			<div className="container py-4 flex items-center justify-between gap-4">
				<div>
					<h1 className="text-2xl md:text-3xl font-bold text-off-90 font-display">{title}</h1>
					<p className="text-off-70 text-sm">{subtitle}</p>
				</div>
				<div className="flex items-center gap-3 w-full max-w-xl ml-auto">
					<div className="relative flex-1">
						<Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/60" aria-hidden />
						<input
							value={q}
							onChange={(e) => onQueryChange(e.target.value)}
							placeholder="Search stories, authors, genres…"
							className="w-full pl-9 pr-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-purple-500"
							aria-label="Search stories"
						/>
					</div>
					<button className="px-3 h-10 rounded-lg border border-white/10 bg-white/5 text-white hover:bg-white/10 inline-flex items-center gap-2" aria-label="Open filters">
						<SlidersHorizontal className="w-4 h-4" />
						<span className="hidden sm:inline">Filters</span>
					</button>
					{toolbar}
				</div>
			</div>
		</div>
	);
}



