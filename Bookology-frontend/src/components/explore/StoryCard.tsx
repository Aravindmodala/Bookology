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
				className={`relative rounded-xl overflow-hidden card-surface group ${highlightGold ? 'gold-ring' : ''}`}
				style={{ perspective: 1000 }}
				onMouseMove={(e) => {
					const rect = (e.currentTarget as HTMLDivElement).getBoundingClientRect();
					x.set(e.clientX - rect.left - rect.width / 2);
					y.set(e.clientY - rect.top - rect.height / 2);
				}}
				onMouseLeave={() => {
					x.set(0); y.set(0);
				}}
				whileHover={{ scale: 1.02 }}
			>
				<motion.div style={{ rotateX: springX, rotateY: springY }} className="h-60">
					<img
						src={story.coverUrl}
						alt={story.title}
						loading="lazy"
						className="w-full h-full object-cover"
					/>
					<div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/20 to-transparent" />
					<div className="absolute top-2 left-2"><GenrePill genre={story.genre} /></div>
				</motion.div>
				<div className="absolute bottom-0 inset-x-0 p-3 flex items-end justify-between">
					<div>
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



