import React from 'react';

export function HeroSkeleton() {
	return (
		<div className="relative h-[70vh] rounded-2xl overflow-hidden card-surface animate-pulse">
			<div className="absolute inset-0 bg-gradient-to-b from-black/40 to-black/80" />
		</div>
	);
}

export function GridSkeleton({ count = 8 }: { count?: number }) {
	return (
		<div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
			{Array.from({ length: count }).map((_, i) => (
				<div key={i} className="h-60 rounded-xl card-surface animate-pulse" />
			))}
		</div>
	);
}



