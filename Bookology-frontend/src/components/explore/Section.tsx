import React from 'react';
import { motion } from 'framer-motion';

type Props = {
	title: string;
	actionSlot?: React.ReactNode;
	children: React.ReactNode;
};

export default function Section({ title, actionSlot, children }: Props) {
	return (
		<section className="py-8">
			<div className="container mb-4 flex items-end justify-between">
				<h2 className="text-xl md:text-2xl font-display font-semibold text-off-90">{title}</h2>
				{actionSlot}
			</div>
			<motion.div
				initial={{ opacity: 0, y: 16 }}
				whileInView={{ opacity: 1, y: 0 }}
				viewport={{ once: true, margin: '-10% 0px' }}
				transition={{ duration: 0.5 }}
			>
				{children}
			</motion.div>
		</section>
	);
}



