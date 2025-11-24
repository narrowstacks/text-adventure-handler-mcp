import { forwardRef, type ReactNode } from 'react';
import { motion, type HTMLMotionProps } from 'framer-motion';
import { Card, type CardProps } from '@mui/material';
import { useReducedMotion, getCardVariants } from '../utils/animations';

// Create motion-enabled MUI Card
const MotionCard = motion.create(Card);

interface AnimatedCardProps extends Omit<CardProps, keyof HTMLMotionProps<'div'> | 'children'> {
    children?: ReactNode;
    delay?: number;
    disableHover?: boolean;
    glowColor?: string;
}

export const AnimatedCard = forwardRef<HTMLDivElement, AnimatedCardProps>(
    ({ children, delay = 0, disableHover = false, glowColor, sx, ...props }, ref) => {
        const reducedMotion = useReducedMotion();
        const variants = getCardVariants(reducedMotion);

        return (
            <MotionCard
                ref={ref}
                initial="hidden"
                animate="visible"
                variants={variants}
                transition={{ delay }}
                whileHover={
                    disableHover || reducedMotion
                        ? undefined
                        : {
                              y: -4,
                              boxShadow: glowColor
                                  ? `0 20px 40px rgba(0, 0, 0, 0.3), 0 0 30px ${glowColor}`
                                  : '0 20px 40px rgba(0, 0, 0, 0.3)',
                              transition: { duration: 0.2 }
                          }
                }
                sx={{
                    cursor: disableHover ? 'default' : 'pointer',
                    ...sx
                }}
                {...props}
            >
                {children}
            </MotionCard>
        );
    }
);

AnimatedCard.displayName = 'AnimatedCard';

export default AnimatedCard;
