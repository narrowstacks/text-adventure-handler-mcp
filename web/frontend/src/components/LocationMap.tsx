import { useMemo } from 'react';
import { motion } from 'framer-motion';
import { Box, Typography, Tooltip } from '@mui/material';
import type { Location } from '../types';
import { useReducedMotion } from '../utils/animations';

interface LocationMapProps {
    locations: Location[];
    currentLocation: string;
}

interface TreeNode {
    location: Location;
    depth: number;
    x: number;
    y: number;
    parent: string | null;
    distanceFromCurrent: number;
}

// Calculate shortest distance from current location using BFS
function calculateDistances(locations: Location[], currentLocation: string): Map<string, number> {
    const distances = new Map<string, number>();
    const locationMap = new Map(locations.map((l) => [l.name, l]));

    // BFS from current location
    const queue: Array<{ name: string; dist: number }> = [{ name: currentLocation, dist: 0 }];
    distances.set(currentLocation, 0);

    while (queue.length > 0) {
        const { name, dist } = queue.shift()!;
        const loc = locationMap.get(name);
        if (!loc) continue;

        for (const neighbor of loc.connected_to || []) {
            if (!distances.has(neighbor)) {
                distances.set(neighbor, dist + 1);
                queue.push({ name: neighbor, dist: dist + 1 });
            }
        }
    }

    // Mark unreachable locations with high distance
    locations.forEach((loc) => {
        if (!distances.has(loc.name)) {
            distances.set(loc.name, 999);
        }
    });

    return distances;
}

// Build tree structure using BFS from root
function buildTree(
    locations: Location[],
    currentLocation: string
): { nodes: Map<string, TreeNode>; connections: Array<{ from: string; to: string }> } {
    const nodes = new Map<string, TreeNode>();
    const connections: Array<{ from: string; to: string }> = [];
    const locationMap = new Map(locations.map((l) => [l.name, l]));

    if (locations.length === 0) return { nodes, connections };

    // Find root: oldest location by created_at, or first in array
    const sortedByCreated = [...locations].sort(
        (a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    );
    const root = sortedByCreated[0];

    // Calculate distances from current location for fading
    const distances = calculateDistances(locations, currentLocation);

    // BFS to assign depths and build tree
    const visited = new Set<string>();
    const levelNodes: Map<number, string[]> = new Map();
    const queue: Array<{ name: string; depth: number; parent: string | null }> = [
        { name: root.name, depth: 0, parent: null }
    ];
    visited.add(root.name);

    while (queue.length > 0) {
        const { name, depth, parent } = queue.shift()!;
        const loc = locationMap.get(name);
        if (!loc) continue;

        // Track nodes at each level
        if (!levelNodes.has(depth)) {
            levelNodes.set(depth, []);
        }
        levelNodes.get(depth)!.push(name);

        // Create tree node (position calculated later)
        nodes.set(name, {
            location: loc,
            depth,
            x: 0,
            y: 0,
            parent,
            distanceFromCurrent: distances.get(name) ?? 999
        });

        // Add connection to parent
        if (parent) {
            connections.push({ from: parent, to: name });
        }

        // Queue children
        for (const neighbor of loc.connected_to || []) {
            if (!visited.has(neighbor) && locationMap.has(neighbor)) {
                visited.add(neighbor);
                queue.push({ name: neighbor, depth: depth + 1, parent: name });
            }
        }
    }

    // Handle disconnected locations - add them at the bottom
    let maxDepth = Math.max(...Array.from(levelNodes.keys()), 0);
    locations.forEach((loc) => {
        if (!visited.has(loc.name)) {
            maxDepth += 1;
            if (!levelNodes.has(maxDepth)) {
                levelNodes.set(maxDepth, []);
            }
            levelNodes.get(maxDepth)!.push(loc.name);
            nodes.set(loc.name, {
                location: loc,
                depth: maxDepth,
                x: 0,
                y: 0,
                parent: null,
                distanceFromCurrent: distances.get(loc.name) ?? 999
            });
        }
    });

    // Calculate positions
    const levelHeight = 70;
    const nodeSpacing = 90;
    const maxWidth = Math.max(...Array.from(levelNodes.values()).map((arr) => arr.length));
    const svgWidth = Math.max(280, maxWidth * nodeSpacing);

    levelNodes.forEach((names, depth) => {
        const count = names.length;
        const levelWidth = count * nodeSpacing;
        const startX = (svgWidth - levelWidth) / 2 + nodeSpacing / 2;

        names.forEach((name, index) => {
            const node = nodes.get(name);
            if (node) {
                node.x = startX + index * nodeSpacing;
                node.y = 30 + depth * levelHeight;
            }
        });
    });

    return { nodes, connections };
}

export default function LocationMap({ locations, currentLocation }: LocationMapProps) {
    const reducedMotion = useReducedMotion();

    // Build tree layout
    const { nodes, connections } = useMemo(
        () => buildTree(locations, currentLocation),
        [locations, currentLocation]
    );

    // Calculate SVG dimensions based on tree
    const dimensions = useMemo(() => {
        if (nodes.size === 0) return { width: 280, height: 200 };
        let maxX = 0,
            maxY = 0;
        nodes.forEach((node) => {
            maxX = Math.max(maxX, node.x);
            maxY = Math.max(maxY, node.y);
        });
        return {
            width: Math.max(280, maxX + 60),
            height: Math.max(200, maxY + 50)
        };
    }, [nodes]);

    // Get opacity based on distance from current location
    const getOpacity = (distance: number): number => {
        if (distance === 0) return 1; // Current location
        if (distance === 1) return 1; // Adjacent
        if (distance >= 999) return 0.25; // Unreachable
        return Math.max(0.35, 1 - distance * 0.2);
    };

    if (locations.length === 0) {
        return (
            <Box
                sx={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    height: 200,
                    color: 'text.secondary'
                }}
            >
                <Typography variant="body2">No locations discovered</Typography>
            </Box>
        );
    }

    // Convert nodes Map to array for rendering
    const nodeArray = Array.from(nodes.values());

    return (
        <Box sx={{ width: '100%', display: 'flex', justifyContent: 'center', overflow: 'auto' }}>
            <svg
                width={dimensions.width}
                height={dimensions.height}
                style={{ overflow: 'visible', minWidth: 280 }}
            >
                {/* Connection lines (curved paths from parent to child) */}
                {connections.map(({ from, to }, index) => {
                    const fromNode = nodes.get(from);
                    const toNode = nodes.get(to);
                    if (!fromNode || !toNode) return null;

                    // Calculate opacity based on distance of both ends from current
                    const lineOpacity =
                        Math.min(
                            getOpacity(fromNode.distanceFromCurrent),
                            getOpacity(toNode.distanceFromCurrent)
                        ) * 0.6;

                    // Create curved path (bezier curve for tree-like appearance)
                    const midY = (fromNode.y + toNode.y) / 2;
                    const pathD = `M ${fromNode.x} ${fromNode.y} C ${fromNode.x} ${midY}, ${toNode.x} ${midY}, ${toNode.x} ${toNode.y}`;

                    return (
                        <motion.path
                            key={`${from}-${to}`}
                            d={pathD}
                            fill="none"
                            stroke="rgba(124, 231, 194, 0.5)"
                            strokeWidth={2}
                            strokeOpacity={lineOpacity}
                            initial={reducedMotion ? {} : { pathLength: 0, opacity: 0 }}
                            animate={{ pathLength: 1, opacity: lineOpacity }}
                            transition={{ duration: 0.5, delay: 0.1 + index * 0.05 }}
                        />
                    );
                })}

                {/* Location nodes */}
                {nodeArray.map((node, index) => {
                    const isCurrent = node.location.name === currentLocation;
                    const nodeRadius = isCurrent ? 14 : 10;
                    const opacity = getOpacity(node.distanceFromCurrent);

                    return (
                        <Tooltip
                            key={node.location.id}
                            title={node.location.description || node.location.name}
                            arrow
                        >
                            <g style={{ cursor: 'pointer', opacity }}>
                                {/* Glow effect for current location */}
                                {isCurrent && !reducedMotion && (
                                    <motion.circle
                                        cx={node.x}
                                        cy={node.y}
                                        r={nodeRadius + 8}
                                        fill="none"
                                        stroke="rgba(124, 231, 194, 0.4)"
                                        strokeWidth={2}
                                        initial={{ scale: 0.8, opacity: 0 }}
                                        animate={{
                                            scale: [1, 1.3, 1],
                                            opacity: [0.4, 0.1, 0.4]
                                        }}
                                        transition={{
                                            duration: 2,
                                            repeat: Infinity,
                                            ease: 'easeInOut'
                                        }}
                                    />
                                )}

                                {/* Node circle */}
                                <motion.circle
                                    cx={node.x}
                                    cy={node.y}
                                    r={nodeRadius}
                                    fill={isCurrent ? '#7ce7c2' : '#ff8ba7'}
                                    stroke={isCurrent ? '#7ce7c2' : 'rgba(255, 139, 167, 0.5)'}
                                    strokeWidth={2}
                                    initial={reducedMotion ? {} : { scale: 0, opacity: 0 }}
                                    animate={{ scale: 1, opacity: 1 }}
                                    transition={{
                                        delay: index * 0.05,
                                        type: 'spring',
                                        stiffness: 300
                                    }}
                                    whileHover={{ scale: 1.2 }}
                                    style={{
                                        filter: isCurrent
                                            ? 'drop-shadow(0 0 8px rgba(124, 231, 194, 0.6))'
                                            : 'none'
                                    }}
                                />

                                {/* Location name */}
                                <motion.text
                                    x={node.x}
                                    y={node.y + nodeRadius + 14}
                                    textAnchor="middle"
                                    fill={isCurrent ? '#7ce7c2' : 'rgba(255, 255, 255, 0.7)'}
                                    fontSize={isCurrent ? 11 : 10}
                                    fontWeight={isCurrent ? 600 : 400}
                                    initial={reducedMotion ? {} : { opacity: 0 }}
                                    animate={{ opacity: 1 }}
                                    transition={{ delay: index * 0.05 + 0.2 }}
                                >
                                    {node.location.name.length > 12
                                        ? node.location.name.slice(0, 12) + '...'
                                        : node.location.name}
                                </motion.text>

                                {/* "You are here" indicator */}
                                {isCurrent && (
                                    <motion.text
                                        x={node.x}
                                        y={node.y + 4}
                                        textAnchor="middle"
                                        fill="rgba(0, 0, 0, 0.7)"
                                        fontSize={10}
                                        fontWeight={700}
                                        initial={reducedMotion ? {} : { scale: 0 }}
                                        animate={{ scale: 1 }}
                                        transition={{ delay: 0.3, type: 'spring' }}
                                    >
                                        ★
                                    </motion.text>
                                )}
                            </g>
                        </Tooltip>
                    );
                })}
            </svg>
        </Box>
    );
}
