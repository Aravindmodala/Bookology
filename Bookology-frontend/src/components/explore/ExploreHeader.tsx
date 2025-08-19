import React from 'react';
import { Search } from 'lucide-react';

type ExploreHeaderProps = {
	title?: string;
	subtitle?: string;
	q: string;
	onQueryChange: (q: string) => void;
	toolbar?: React.ReactNode;
};

export default function ExploreHeader({
	title = 'Explore',
	subtitle = 'Discover captivating stories',
	q,
	onQueryChange,
	toolbar,
}: ExploreHeaderProps) {
	return (
		<div className="sticky top-0 z-30 bg-black/70 backdrop-blur-md border-b border-white/10">
			<div className="container py-4 flex items-center justify-between gap-4">
				<div>
					<h1 className="text-2xl md:text-3xl font-display font-semibold tracking-tight text-white whitespace-nowrap">{title}</h1>
					<p className="text-white/60 text-sm">{subtitle}</p>
				</div>
				<div className="flex items-center gap-3 w-full max-w-xl ml-auto">
					<div className="relative flex-1">
						<Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-white/60" aria-hidden />
						<input
							value={q}
							onChange={(e) => onQueryChange(e.target.value)}
							placeholder="Search stories, authors…"
							className="w-full pl-9 pr-3 py-2 rounded-lg bg-white/5 border border-white/10 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-red-500/70"
							aria-label="Search stories"
						/>
					</div>
					{toolbar}
				</div>
			</div>
		</div>
	);
}



