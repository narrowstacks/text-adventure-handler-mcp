import type { Variants } from 'framer-motion';

// Card entrance animation
export const cardEntrance: Variants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.4, ease: 'easeOut' }
    }
};

// Staggered container for lists
export const staggerContainer: Variants = {
    hidden: { opacity: 0 },
    visible: {
        opacity: 1,
        transition: { staggerChildren: 0.08, delayChildren: 0.1 }
    }
};

// List item entrance
export const listItemEntrance: Variants = {
    hidden: { opacity: 0, x: -20 },
    visible: {
        opacity: 1,
        x: 0,
        transition: { duration: 0.3, ease: 'easeOut' }
    },
    exit: {
        opacity: 0,
        x: 20,
        transition: { duration: 0.2 }
    }
};

// Fade in from bottom
export const fadeInUp: Variants = {
    hidden: { opacity: 0, y: 30 },
    visible: {
        opacity: 1,
        y: 0,
        transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }
    }
};

// Scale in
export const scaleIn: Variants = {
    hidden: { opacity: 0, scale: 0.9 },
    visible: {
        opacity: 1,
        scale: 1,
        transition: { duration: 0.3, ease: 'easeOut' }
    }
};

// Pulse animation for highlights
export const pulseAnimation = {
    scale: [1, 1.05, 1],
    transition: { duration: 0.3 }
};

// Glow effect generator
export const glowEffect = (color: string) => ({
    boxShadow: [
        `0 0 0px ${color}`,
        `0 0 20px ${color}`,
        `0 0 0px ${color}`
    ],
    transition: { duration: 0.6, ease: 'easeInOut' }
});

// Dice roll animation
export const diceRoll: Variants = {
    rolling: {
        rotate: [0, 360, 720, 1080],
        scale: [1, 1.2, 0.9, 1.1, 1],
        transition: { duration: 0.8, ease: 'easeOut' }
    },
    stopped: {
        rotate: 0,
        scale: 1
    }
};

// Number counter animation
export const numberChange: Variants = {
    initial: { y: 0, opacity: 1 },
    increase: {
        y: [-10, 0],
        opacity: [0, 1],
        color: ['#7ce7c2', 'inherit'],
        transition: { duration: 0.4 }
    },
    decrease: {
        y: [10, 0],
        opacity: [0, 1],
        color: ['#ff6b6b', 'inherit'],
        transition: { duration: 0.4 }
    }
};

// Hook to check for reduced motion preference
export const useReducedMotion = (): boolean => {
    if (typeof window === 'undefined') return false;
    const prefersReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    return prefersReduced;
};

// Get animation variants based on reduced motion
export const getCardVariants = (reducedMotion: boolean): Variants => {
    if (reducedMotion) {
        return {
            hidden: { opacity: 0 },
            visible: { opacity: 1, transition: { duration: 0.1 } }
        };
    }
    return cardEntrance;
};

// Hover animation presets
export const hoverLift = {
    y: -4,
    boxShadow: '0 20px 40px rgba(0, 0, 0, 0.3)',
    transition: { duration: 0.2 }
};

export const hoverGlow = (color: string = 'rgba(124, 231, 194, 0.3)') => ({
    boxShadow: `0 0 30px ${color}`,
    transition: { duration: 0.3 }
});
