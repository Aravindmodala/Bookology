import React, { useMemo, useRef, useState } from 'react';
import { motion, useMotionValue, useSpring } from 'framer-motion';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import GenrePill from './GenrePill';
import type { Story } from './StoryCard';
import { Link } from 'react-router-dom';

type Props = { stories: Story[] };

export default function HeroCarousel({ stories }: Props) {
	const [index, setIndex] = useState(0);
	const current = stories?.[index];
	const x = useMotionValue(0);
	const y = useMotionValue(0);
	const springX = useSpring(x, { stiffness: 60, damping: 10 });
	const springY = useSpring(y, { stiffness: 60, damping: 10 });

	function onNav(dir: number) {
		setIndex((prev) => (prev + dir + stories.length) % stories.length);
	}

	if (!current) return null;

	return (
		<div className="relative h-[70vh] md:h-[78vh] rounded-2xl overflow-hidden card-surface">
			<motion.img
				src={current.coverUrl}
				alt={current.title}
				className="absolute inset-0 w-full h-full object-cover"
				style={{ x: springX, y: springY }}
				decoding="async"
				fetchpriority="high"
				onMouseMove={(e) => {
					const rect = (e.currentTarget as HTMLImageElement).getBoundingClientRect();
					x.set((e.clientX - rect.left - rect.width / 2) / 8);
					y.set((e.clientY - rect.top - rect.height / 2) / 8);
				}}
				onMouseLeave={() => { x.set(0); y.set(0); }}
			/>
			<div className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/40 to-transparent" />
			<div className="absolute inset-x-0 bottom-0 p-6 md:p-10">
				<div className="mb-3"><GenrePill genre={current.genre} /></div>
				<h2 className="text-3xl md:text-5xl font-display font-bold text-white max-w-3xl drop-shadow">{current.title}</h2>
				{current.subtitle && <p className="text-white/80 mt-2 max-w-2xl">{current.subtitle}</p>}
				<div className="mt-4 flex items-center gap-3">
					{current.author?.avatarUrl ? (
						<img src={current.author.avatarUrl} alt={current.author.name} className="w-8 h-8 rounded-full" />
					) : (
						<div className="w-8 h-8 rounded-full bg-white/20" aria-hidden />
					)}
					<span className="text-white/80 text-sm">{current.author?.name}</span>
					<Link to={`/story/${current.id}`} className="ml-4 px-4 py-2 rounded-lg bg-white text-black font-semibold shadow">
						Read
					</Link>
				</div>
			</div>

			{/* Arrows */}
			<button aria-label="Previous" className="absolute left-3 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/40 text-white hover:bg-black/60" onClick={() => onNav(-1)}>
				<ChevronLeft className="w-5 h-5" />
			</button>
			<button aria-label="Next" className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-full bg-black/40 text-white hover:bg-black/60" onClick={() => onNav(1)}>
				<ChevronRight className="w-5 h-5" />
			</button>
		</div>
	);
}



