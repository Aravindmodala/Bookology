import React from 'react';
import { motion } from 'framer-motion';

const transition = { duration: 0.4, ease: [0.22, 1, 0.36, 1] };

export default function Page({ children, className = '' }) {
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 16, filter: 'blur(2px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      exit={{ opacity: 0, y: -16, filter: 'blur(2px)' }}
      transition={transition}
      style={{ willChange: 'transform, opacity, filter' }}
    >
      {children}
    </motion.div>
  );
}


