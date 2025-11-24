export interface StatDefinition {
    name: string;
    description: string;
    default_value: number;
    min_value: number;
    max_value: number;
}

export interface Adventure {
    id: string;
    title: string;
    description: string;
    stats: StatDefinition[];
    starting_hp: number;
    initial_location: string;
    initial_story: string;
    // ... other fields as needed
}

export interface InventoryItem {
    id: string;
    name: string;
    description: string;
    quantity: number;
    properties: Record<string, any>;
}

export interface QuestStatus {
    id: string;
    title: string;
    description: string;
    status: string;
    objectives: string[];
    completed_objectives: string[];
    rewards: Record<string, any>;
}

export interface PlayerState {
    session_id: string;
    hp: number;
    max_hp: number;
    score: number;
    location: string;
    stats: Record<string, number>;
    inventory: InventoryItem[];
    quests: QuestStatus[];
    relationships: Record<string, number>;
    custom_data: Record<string, any>;
    currency: number;
    game_time: number;
    game_day: number;
}

export interface GameSession {
    id: string;
    adventure_id: string;
    adventure_title?: string; // Joined field
    created_at: string;
    last_played: string;
    state?: PlayerState; // Joined/Fetched field
    adventure?: Adventure; // Fetched field
}

export interface ActionHistory {
    id?: number;
    session_id: string;
    action_text: string;
    stat_used?: string;
    dice_roll: {
        roll: number;
        modifier: number;
        total: number;
        dc?: number;
        success?: boolean;
        message?: string;
    };
    outcome: string;
    score_change: number;
    timestamp: string;
}
