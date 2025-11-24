import { useEffect, useRef } from 'react';
import confetti from 'canvas-confetti';
import type { QuestStatus } from '../types';

// Adventure-themed colors
const CONFETTI_COLORS = ['#7ce7c2', '#ff8ba7', '#f0c75e', '#5fe0ff', '#c792ea'];

export const triggerQuestConfetti = () => {
    // Fire from both sides
    const end = Date.now() + 500;

    const frame = () => {
        confetti({
            particleCount: 3,
            angle: 60,
            spread: 55,
            origin: { x: 0, y: 0.7 },
            colors: CONFETTI_COLORS
        });

        confetti({
            particleCount: 3,
            angle: 120,
            spread: 55,
            origin: { x: 1, y: 0.7 },
            colors: CONFETTI_COLORS
        });

        if (Date.now() < end) {
            requestAnimationFrame(frame);
        }
    };

    frame();
};

export const triggerLevelUpConfetti = () => {
    // Big central burst
    confetti({
        particleCount: 150,
        spread: 100,
        origin: { y: 0.6 },
        colors: CONFETTI_COLORS,
        startVelocity: 45,
        gravity: 0.8,
        scalar: 1.2
    });
};

export const triggerScoreConfetti = (x: number = 0.5, y: number = 0.5) => {
    // Small localized burst
    confetti({
        particleCount: 30,
        spread: 60,
        origin: { x, y },
        colors: ['#7ce7c2', '#f0c75e'],
        startVelocity: 25,
        gravity: 1.2,
        scalar: 0.8,
        ticks: 100
    });
};

// Hook to detect quest completion and trigger confetti
export function useQuestCompletion(quests: QuestStatus[] | undefined) {
    const prevCompletedRef = useRef<Set<string>>(new Set());

    useEffect(() => {
        if (!quests) return;

        const currentCompleted = new Set(
            quests.filter((q) => q.status === 'completed').map((q) => q.id)
        );

        // Check for newly completed quests
        let newlyCompleted = false;
        currentCompleted.forEach((id) => {
            if (!prevCompletedRef.current.has(id)) {
                newlyCompleted = true;
            }
        });

        if (newlyCompleted) {
            triggerQuestConfetti();
        }

        prevCompletedRef.current = currentCompleted;
    }, [quests]);
}

// Hook to detect score increases and trigger small celebration
export function useScoreCelebration(score: number | undefined) {
    const prevScoreRef = useRef<number | null>(null);

    useEffect(() => {
        if (score === undefined) return;

        if (prevScoreRef.current !== null && score > prevScoreRef.current) {
            const increase = score - prevScoreRef.current;
            // Only celebrate significant score increases
            if (increase >= 50) {
                triggerScoreConfetti();
            }
        }

        prevScoreRef.current = score;
    }, [score]);
}

export default {
    triggerQuestConfetti,
    triggerLevelUpConfetti,
    triggerScoreConfetti,
    useQuestCompletion,
    useScoreCelebration
};
