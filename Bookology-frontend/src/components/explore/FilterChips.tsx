import React from 'react';
import { motion } from 'framer-motion';

export type Filters = {
	genres: string[];
	mood?: string;
	length?: 'short'|'medium'|'long';
	sort?: 'trending'|'newest'|'mostLiked'|'mostViewed';
	q?: string;
};

type Props = {
	filters: Filters;
	onChange: (f: Filters) => void;
};

const genreOptions = ['fantasy','sci-fi','thriller','romance','adventure','mystery','drama','horror'];
const sortOptions: Filters['sort'][] = ['trending','newest','mostLiked','mostViewed'];

export default function FilterChips({ filters, onChange }: Props) {
	function toggleGenre(g: string) {
		const set = new Set(filters.genres || []);
		set.has(g) ? set.delete(g) : set.add(g);
		onChange({ ...filters, genres: Array.from(set) });
	}

	return (
		<div className="flex flex-wrap gap-2">
			{genreOptions.map((g) => {
				const active = filters.genres?.includes(g);
				return (
					<motion.button
						whileTap={{ scale: 0.95 }}
						key={g}
						onClick={() => toggleGenre(g)}
						className={`chip ${active ? 'chip-active' : ''}`}
						aria-pressed={active}
					>
						{g}
					</motion.button>
				);
			})}
			<div className="mx-2" />
			{sortOptions.map((s) => (
				<motion.button
					whileTap={{ scale: 0.95 }}
					key={s}
					onClick={() => onChange({ ...filters, sort: s })}
					className={`chip ${filters.sort === s ? 'chip-active' : ''}`}
					aria-pressed={filters.sort === s}
				>
					{s}
				</motion.button>
			))}
		</div>
	);
}



