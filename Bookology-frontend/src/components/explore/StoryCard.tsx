import React, { memo } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { Heart, Eye, MessageCircle } from 'lucide-react';
import GenrePill from './GenrePill';
import { Link } from 'react-router-dom';

export type Story = {
	id: string;
	title: string;
	subtitle?: string;
	coverUrl: string;
	genre: string;
	author: { id: string; name: string; avatarUrl?: string };
	stats: { views: number; likes: number; comments: number };
	isFeatured?: boolean;
	isPublic: boolean;
	createdAt: string;
  aspectRatio?: number; // width / height
};

type Props = { story: Story; highlightGold?: boolean };

export default memo(function StoryCard({ story, highlightGold }: Props) {
	const x = useMotionValue(0);
	const y = useMotionValue(0);
	const rotateX = useTransform(y, [-50, 50], [8, -8]);
	const rotateY = useTransform(x, [-50, 50], [-8, 8]);
	const springX = useSpring(rotateX, { stiffness: 120, damping: 12 });
	const springY = useSpring(rotateY, { stiffness: 120, damping: 12 });

	return (
		<Link to={`/story/${story.id}`} aria-label={`Open story ${story.title}`}>
			<motion.div
				className={`relative rounded-xl overflow-hidden card-surface group ${highlightGold ? 'gold-ring' : ''} transform-gpu`}
				style={{ perspective: 1000, willChange: 'transform' }}
				onMouseMove={(e) => {
					const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
					x.set(e.clientX - rect.left - rect.width / 2);
					y.set(e.clientY - rect.top - rect.height / 2);
				}}
				onMouseLeave={() => {
					x.set(0); y.set(0);
				}}
				whileHover={{ scale: 1.025 }}
				transition={{ type: 'spring', stiffness: 260, damping: 22, mass: 0.9 }}
			>
				<motion.div style={{ rotateX: springX, rotateY: springY }} className="will-change-transform" >
					<div
						src={story.coverUrl}
						style={{
							aspectRatio: (story.aspectRatio && story.aspectRatio > 0) ? `${story.aspectRatio} / 1` : undefined,
						}}
						className="w-full select-none"
					>
						<img
							src={story.coverUrl}
							alt={story.title}
							loading="lazy"
							decoding="async"
							fetchPriority="low"
							className="w-full h-full object-cover"
						/>
					</div>
					<div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
					<div className="absolute top-2 left-2"><GenrePill genre={story.genre} /></div>
					<div className="absolute bottom-0 left-0 right-0 p-3">
						<h3 className="font-display text-lg md:text-xl text-white leading-tight drop-shadow-sm">{story.title}</h3>
					</div>
				</motion.div>
				<div className="absolute bottom-0 inset-x-0 p-3 pt-10 flex items-end justify-between">
					<div className="sr-only">
						<h3 className="text-white font-semibold line-clamp-1">{story.title}</h3>
						<p className="text-white/70 text-xs line-clamp-1">{story.author?.name}</p>
					</div>
					<div className="flex items-center gap-3 text-white/80 text-xs">
						<span className="inline-flex items-center gap-1"><Eye className="w-3 h-3" /> {story.stats?.views ?? 0}</span>
						<span className="inline-flex items-center gap-1"><Heart className="w-3 h-3" /> {story.stats?.likes ?? 0}</span>
						<span className="inline-flex items-center gap-1"><MessageCircle className="w-3 h-3" /> {story.stats?.comments ?? 0}</span>
					</div>
				</div>
			</motion.div>
		</Link>
	);
});



