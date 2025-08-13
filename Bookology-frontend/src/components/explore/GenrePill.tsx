import React from 'react';

const genreClass: Record<string, string> = {
	'fantasy': 'from-[#7C3AED] to-[#C084FC]',
	'sci-fi': 'from-[#00B5D8] to-[#60A5FA]',
	'thriller': 'from-[#F97316] to-[#FB7185]',
	'romance': 'from-[#EC4899] to-[#F472B6]',
	'adventure': 'from-[#F59E0B] to-[#FBBF24]',
	'mystery': 'from-[#22D3EE] to-[#7DD3FC]',
	'horror': 'from-[#EF4444] to-[#F59E0B]',
	'drama': 'from-[#8B5CF6] to-[#14B8A6]',
};

type Props = { genre: string };

export default function GenrePill({ genre }: Props) {
	const gradient = genreClass[genre?.toLowerCase?.()] || 'from-white/40 to-white/20';
	return (
		<span className={`inline-flex items-center px-2 py-1 text-xs rounded-full bg-gradient-to-r ${gradient} text-black/90 font-semibold backdrop-blur-sm`}>
			{(genre || 'Genre').toUpperCase()}
		</span>
	);
}



