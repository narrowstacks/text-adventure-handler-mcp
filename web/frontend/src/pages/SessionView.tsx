import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { motion, AnimatePresence } from "framer-motion";
import Grid from "@mui/material/GridLegacy";
import {
  Box,
  Typography,
  LinearProgress,
  Card,
  CardContent,
  Stack,
  Chip,
  Divider,
  List,
  ListItem,
  ListItemText,
  Tooltip,
} from "@mui/material";
import FavoriteIcon from "@mui/icons-material/Favorite";
import LocationOnIcon from "@mui/icons-material/LocationOn";
import TimelineIcon from "@mui/icons-material/Timeline";
import PeopleIcon from "@mui/icons-material/PeopleAlt";
import MapIcon from "@mui/icons-material/Map";
import ShieldIcon from "@mui/icons-material/Shield";
import QueryStatsIcon from "@mui/icons-material/QueryStats";
import HandshakeIcon from "@mui/icons-material/Handshake";
import {
  getNarratorThoughts,
  getSession,
  getSessionHistory,
  getSessionSummaries,
  getSessionWorld,
} from "../api";
import { useAppStore } from "../store";
import HistoryLog from "../components/HistoryLog";
import QuestTracker from "../components/QuestTracker";
import InventoryList from "../components/InventoryList";
import { AnimatedCard } from "../components/AnimatedCard";
import StatBar from "../components/StatBar";
import LocationMap from "../components/LocationMap";
import RelationshipGraph from "../components/RelationshipGraph";
import { CardSkeleton, HistoryEntrySkeleton, StatsSkeleton } from "../components/Skeletons";
import { useScoreCelebration } from "../components/Confetti";
import { useReducedMotion, fadeInUp, staggerContainer } from "../utils/animations";

export default function SessionView() {
  const { id } = useParams<{ id: string }>();
  const { setAdventureTheme } = useAppStore();

  const sessionQuery = useQuery({
    queryKey: ["session", id],
    queryFn: () => getSession(id!),
    enabled: !!id,
    refetchInterval: 5000,
  });

  const worldQuery = useQuery({
    queryKey: ["world", id],
    queryFn: () => getSessionWorld(id!),
    enabled: !!id,
    refetchInterval: 8000,
  });

  const historyQuery = useQuery({
    queryKey: ["history", id],
    queryFn: () => getSessionHistory(id!, 120),
    enabled: !!id,
    refetchInterval: 4000,
  });

  const summariesQuery = useQuery({
    queryKey: ["summaries", id],
    queryFn: () => getSessionSummaries(id!),
    enabled: !!id,
    refetchInterval: 10000,
  });

  const thoughtsQuery = useQuery({
    queryKey: ["thoughts", id],
    queryFn: () => getNarratorThoughts(id!),
    enabled: !!id,
  });

  useEffect(() => {
    if (sessionQuery.data?.adventure?.title) {
      setAdventureTheme(sessionQuery.data.adventure.title);
    }
    return () => setAdventureTheme(null);
  }, [sessionQuery.data?.adventure?.title, setAdventureTheme]);

  const reducedMotion = useReducedMotion();
  const [prevHp, setPrevHp] = useState<number | null>(null);
  const [hpAnimation, setHpAnimation] = useState<'none' | 'increase' | 'decrease'>('none');

  const loading =
    sessionQuery.isLoading ||
    worldQuery.isLoading ||
    historyQuery.isLoading ||
    summariesQuery.isLoading;

  const session = sessionQuery.data;
  const state = session?.state;
  const adventure = session?.adventure;
  const world = worldQuery.data;

  // Trigger celebrations for score increases
  useScoreCelebration(state?.score);

  // Track HP changes for animation
  useEffect(() => {
    if (state?.hp !== undefined) {
      if (prevHp !== null && state.hp !== prevHp) {
        setHpAnimation(state.hp > prevHp ? 'increase' : 'decrease');
        // Reset animation after 600ms
        const timeout = setTimeout(() => setHpAnimation('none'), 600);
        return () => clearTimeout(timeout);
      }
      setPrevHp(state.hp);
    }
  }, [state?.hp, prevHp]);

  if (loading) {
    return (
      <Stack spacing={3}>
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          <Box>
            <Typography variant="overline" color="text.secondary">Loading...</Typography>
            <Typography variant="h3">Session</Typography>
          </Box>
        </Box>
        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            <CardSkeleton />
            <Box sx={{ mt: 2 }}><StatsSkeleton /></Box>
          </Grid>
          <Grid item xs={12} md={5}>
            <Card><CardContent><HistoryEntrySkeleton count={4} /></CardContent></Card>
          </Grid>
          <Grid item xs={12} md={4}>
            <CardSkeleton />
          </Grid>
        </Grid>
      </Stack>
    );
  }

  if (!session || !state) {
    return <Typography>Session not found</Typography>;
  }

  // Calculate HP color
  const hpPercent = (state.hp / Math.max(state.max_hp, 1)) * 100;
  const hpColor = hpPercent > 60 ? "#7ce7c2" : hpPercent > 30 ? "#f0c75e" : "#ff6b6b";
  const hasRelationships = Object.keys(state.relationships || {}).length > 0;

  return (
    <motion.div
      initial={reducedMotion ? false : "hidden"}
      animate="visible"
      variants={staggerContainer}
    >
      <Stack spacing={3}>
        <motion.div variants={fadeInUp}>
          <Box
            sx={{ display: "flex", alignItems: "center", gap: 2, flexWrap: "wrap" }}
          >
            <Box>
              <Typography variant="overline" color="text.secondary">
                {adventure?.title}
              </Typography>
              <Typography variant="h3">Session {session.id.slice(0, 8)}</Typography>
              <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap" useFlexGap>
                <Tooltip title="Current Location">
                  <Chip
                    icon={<LocationOnIcon />}
                    label={state.location}
                    color="secondary"
                    sx={{ fontWeight: 500 }}
                  />
                </Tooltip>
                <motion.div
                  animate={reducedMotion ? {} : {
                    scale: state.score > 0 ? [1, 1.1, 1] : 1
                  }}
                  transition={{ duration: 0.3 }}
                >
                  <Chip
                    label={`Score ${state.score}`}
                    size="small"
                    sx={{ bgcolor: "rgba(124, 231, 194, 0.15)", fontWeight: 600 }}
                  />
                </motion.div>
                <Chip
                  label={`Day ${state.game_day} • ${String(state.game_time).padStart(2, '0')}:00`}
                  size="small"
                  variant="outlined"
                />
                {state.currency > 0 && (
                  <Chip
                    label={`${state.currency} gold`}
                    size="small"
                    sx={{ bgcolor: "rgba(240, 199, 94, 0.15)" }}
                  />
                )}
              </Stack>
            </Box>
          </Box>
        </motion.div>

        <Grid container spacing={2}>
          <Grid item xs={12} md={3}>
            {/* Vitality Card with HP animation */}
            <motion.div variants={fadeInUp}>
              <AnimatedCard sx={{ mb: 2 }} disableHover>
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Vitality
                  </Typography>
                  <Stack
                    direction="row"
                    spacing={1}
                    alignItems="center"
                    sx={{ mb: 1 }}
                  >
                    <motion.div
                      animate={reducedMotion || hpAnimation === 'none' ? {} : {
                        scale: [1, 1.3, 1],
                        color: hpAnimation === 'increase' ? ["#ff6b6b", "#7ce7c2", hpColor] : [hpColor, "#ff6b6b", hpColor]
                      }}
                      transition={{ duration: 0.5 }}
                    >
                      <FavoriteIcon sx={{ color: hpColor }} />
                    </motion.div>
                    <AnimatePresence mode="wait">
                      <motion.div
                        key={state.hp}
                        initial={reducedMotion ? {} : { y: hpAnimation === 'increase' ? 10 : -10, opacity: 0 }}
                        animate={{ y: 0, opacity: 1 }}
                        exit={{ y: hpAnimation === 'increase' ? -10 : 10, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <Typography variant="h5" sx={{ color: hpColor, fontWeight: 600 }}>
                          {state.hp} / {state.max_hp}
                        </Typography>
                      </motion.div>
                    </AnimatePresence>
                  </Stack>
                  <motion.div
                    animate={reducedMotion || hpAnimation === 'none' ? {} : {
                      boxShadow: hpAnimation === 'increase'
                        ? ["0 0 0px transparent", `0 0 15px ${hpColor}`, "0 0 0px transparent"]
                        : ["0 0 0px transparent", "0 0 15px #ff6b6b", "0 0 0px transparent"]
                    }}
                    transition={{ duration: 0.6 }}
                    style={{ borderRadius: 5 }}
                  >
                    <LinearProgress
                      variant="determinate"
                      value={hpPercent}
                      sx={{
                        height: 10,
                        borderRadius: 5,
                        bgcolor: "rgba(255,255,255,0.1)",
                        "& .MuiLinearProgress-bar": {
                          bgcolor: hpColor,
                          transition: "transform 0.5s ease, background-color 0.3s ease"
                        }
                      }}
                    />
                  </motion.div>
                </CardContent>
              </AnimatedCard>
            </motion.div>

            {/* Stat Profile with animated bars */}
            <motion.div variants={fadeInUp}>
              <AnimatedCard sx={{ mb: 2 }} disableHover delay={0.1}>
                <CardContent>
                  <Typography
                    variant="subtitle2"
                    color="text.secondary"
                    gutterBottom
                  >
                    Stat Profile
                  </Typography>
                  <Stack spacing={1}>
                    {Object.entries(state.stats).map(([key, value]) => (
                      <StatBar
                        key={key}
                        name={key}
                        value={value}
                        maxValue={20}
                      />
                    ))}
                  </Stack>
                </CardContent>
              </AnimatedCard>
            </motion.div>

            {/* Resources */}
            <motion.div variants={fadeInUp}>
              <AnimatedCard sx={{ mb: 2 }} disableHover delay={0.2}>
                <CardContent>
                  <Typography
                    variant="subtitle2"
                    color="text.secondary"
                    gutterBottom
                  >
                    Resources
                  </Typography>
                  <Stack spacing={0.5}>
                    <Typography variant="body2">
                      <strong>Currency:</strong> {state.currency} gold
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Last played: {new Date(session.last_played).toLocaleString()}
                    </Typography>
                  </Stack>
                </CardContent>
              </AnimatedCard>
            </motion.div>

            {/* Relationships */}
            {hasRelationships && (
              <motion.div variants={fadeInUp}>
                <AnimatedCard sx={{ mb: 2 }} disableHover delay={0.25}>
                  <CardContent>
                    <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 1.5 }}>
                      <HandshakeIcon color="primary" sx={{ fontSize: 20 }} />
                      <Typography variant="subtitle2" color="text.secondary">
                        Relationships
                      </Typography>
                    </Stack>
                    <RelationshipGraph relationships={state.relationships} />
                  </CardContent>
                </AnimatedCard>
              </motion.div>
            )}

            <InventoryList inventory={state.inventory} />
            <QuestTracker quests={state.quests} />
          </Grid>

          {/* Actions History */}
          <Grid item xs={12} md={5}>
            <motion.div variants={fadeInUp}>
              <AnimatedCard sx={{ mb: 2 }} disableHover>
                <CardContent>
                  <Stack
                    direction="row"
                    spacing={1}
                    alignItems="center"
                    sx={{ mb: 1 }}
                  >
                    <TimelineIcon color="secondary" />
                    <Typography variant="h6">Recent Actions</Typography>
                    <Chip
                      label={historyQuery.data?.length || 0}
                      size="small"
                      sx={{ ml: "auto", height: 20, fontSize: "0.7rem" }}
                    />
                  </Stack>
                  <HistoryLog history={historyQuery.data || []} />
                </CardContent>
              </AnimatedCard>
            </motion.div>

            <motion.div variants={fadeInUp}>
              <AnimatedCard disableHover delay={0.1}>
                <CardContent>
                  <Stack
                    direction="row"
                    spacing={1}
                    alignItems="center"
                    sx={{ mb: 1 }}
                  >
                    <QueryStatsIcon color="primary" />
                    <Typography variant="h6">Session Summaries</Typography>
                  </Stack>
                  {summariesQuery.data && summariesQuery.data.length > 0 ? (
                    <List dense>
                      {summariesQuery.data.map((s, index) => (
                        <motion.div
                          key={s.id}
                          initial={reducedMotion ? {} : { opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.05 }}
                        >
                          <ListItem alignItems="flex-start" sx={{ px: 0 }}>
                            <ListItemText
                              primary={s.summary}
                              secondary={
                                s.key_events?.length
                                  ? `Key events: ${s.key_events.join(", ")}`
                                  : null
                              }
                              slotProps={{
                                primary: { sx: { fontSize: "0.9rem", lineHeight: 1.5 } },
                                secondary: { sx: { fontSize: "0.8rem", mt: 0.5 } }
                              }}
                            />
                          </ListItem>
                          {index < summariesQuery.data.length - 1 && (
                            <Divider sx={{ my: 1 }} />
                          )}
                        </motion.div>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No summaries yet.
                    </Typography>
                  )}
                </CardContent>
              </AnimatedCard>
            </motion.div>
          </Grid>

          {/* Right Column: World State */}
          <Grid item xs={12} md={4}>
            {/* Characters */}
            <motion.div variants={fadeInUp}>
              <AnimatedCard sx={{ mb: 2 }} disableHover>
                <CardContent>
                  <Stack
                    direction="row"
                    spacing={1}
                    alignItems="center"
                    sx={{ mb: 1 }}
                  >
                    <PeopleIcon color="secondary" />
                    <Typography variant="h6">Characters</Typography>
                    {world?.characters && world.characters.length > 0 && (
                      <Chip
                        label={world.characters.length}
                        size="small"
                        sx={{ ml: "auto", height: 20, fontSize: "0.7rem" }}
                      />
                    )}
                  </Stack>
                  {world?.characters && world.characters.length > 0 ? (
                    <Stack spacing={1}>
                      {world.characters.slice(0, 6).map((c, index) => (
                        <motion.div
                          key={c.id}
                          initial={reducedMotion ? {} : { opacity: 0, y: 10 }}
                          animate={{ opacity: 1, y: 0 }}
                          transition={{ delay: index * 0.03 }}
                        >
                          <Box
                            sx={{
                              p: 1,
                              borderRadius: 1,
                              bgcolor: "rgba(255,255,255,0.03)",
                              border: "1px solid rgba(255,255,255,0.05)",
                            }}
                          >
                            <Typography variant="subtitle2" fontWeight={600}>
                              {c.name}
                            </Typography>
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              sx={{ fontSize: "0.8rem" }}
                            >
                              {c.description.length > 80
                                ? `${c.description.slice(0, 80)}…`
                                : c.description}
                            </Typography>
                            {c.location && (
                              <Chip
                                label={c.location}
                                size="small"
                                sx={{
                                  mt: 0.5,
                                  height: 18,
                                  fontSize: "0.65rem",
                                  bgcolor: "rgba(255, 139, 167, 0.1)",
                                }}
                              />
                            )}
                          </Box>
                        </motion.div>
                      ))}
                    </Stack>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No characters tracked.
                    </Typography>
                  )}
                </CardContent>
              </AnimatedCard>
            </motion.div>

            {/* Locations with Map */}
            <motion.div variants={fadeInUp}>
              <AnimatedCard sx={{ mb: 2 }} disableHover delay={0.1}>
                <CardContent>
                  <Stack
                    direction="row"
                    spacing={1}
                    alignItems="center"
                    sx={{ mb: 1 }}
                  >
                    <MapIcon color="primary" />
                    <Typography variant="h6">Locations</Typography>
                  </Stack>
                  {world?.locations && world.locations.length > 0 ? (
                    <>
                      <LocationMap
                        locations={world.locations}
                        currentLocation={state.location}
                      />
                      <Divider sx={{ my: 2 }} />
                      <Stack spacing={1}>
                        {world.locations.slice(0, 4).map((l) => (
                          <Box
                            key={l.id}
                            sx={{
                              p: 1,
                              border: "1px solid",
                              borderColor:
                                l.name === state.location
                                  ? "primary.main"
                                  : "rgba(255,255,255,0.06)",
                              borderRadius: 1,
                              bgcolor:
                                l.name === state.location
                                  ? "rgba(124, 231, 194, 0.1)"
                                  : "transparent",
                            }}
                          >
                            <Stack direction="row" alignItems="center" spacing={1}>
                              <Typography variant="subtitle2">{l.name}</Typography>
                              {l.name === state.location && (
                                <Chip
                                  label="HERE"
                                  size="small"
                                  sx={{
                                    height: 16,
                                    fontSize: "0.6rem",
                                    bgcolor: "primary.main",
                                    color: "black",
                                    fontWeight: 700,
                                  }}
                                />
                              )}
                            </Stack>
                            <Typography
                              variant="body2"
                              color="text.secondary"
                              sx={{ fontSize: "0.8rem" }}
                            >
                              {l.description.length > 60
                                ? `${l.description.slice(0, 60)}…`
                                : l.description}
                            </Typography>
                          </Box>
                        ))}
                      </Stack>
                    </>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No locations yet.
                    </Typography>
                  )}
                </CardContent>
              </AnimatedCard>
            </motion.div>

            {/* Factions & Status */}
            <motion.div variants={fadeInUp}>
              <AnimatedCard disableHover delay={0.2}>
                <CardContent>
                  <Stack
                    direction="row"
                    spacing={1}
                    alignItems="center"
                    sx={{ mb: 1 }}
                  >
                    <ShieldIcon color="secondary" />
                    <Typography variant="h6">Factions & Status</Typography>
                  </Stack>
                  {world?.factions && world.factions.length > 0 ? (
                    <Stack spacing={1} sx={{ mb: 2 }}>
                      {world.factions.map((f) => (
                        <Box
                          key={f.id}
                          sx={{
                            p: 1,
                            borderRadius: 1,
                            bgcolor: "rgba(255,255,255,0.03)",
                          }}
                        >
                          <Stack direction="row" justifyContent="space-between">
                            <Typography variant="subtitle2">{f.name}</Typography>
                            <Chip
                              label={f.reputation > 0 ? `+${f.reputation}` : f.reputation}
                              size="small"
                              sx={{
                                height: 18,
                                fontSize: "0.65rem",
                                fontWeight: 600,
                                bgcolor:
                                  f.reputation > 0
                                    ? "rgba(124, 231, 194, 0.2)"
                                    : f.reputation < 0
                                      ? "rgba(255, 107, 107, 0.2)"
                                      : "rgba(255,255,255,0.1)",
                                color:
                                  f.reputation > 0
                                    ? "#7ce7c2"
                                    : f.reputation < 0
                                      ? "#ff6b6b"
                                      : "text.secondary",
                              }}
                            />
                          </Stack>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ fontSize: "0.8rem" }}
                          >
                            {f.description}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  ) : (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                      No factions.
                    </Typography>
                  )}

                  {world?.status_effects && world.status_effects.length > 0 && (
                    <>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="subtitle2" sx={{ mb: 1 }}>
                        Status Effects
                      </Typography>
                      <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                        {world.status_effects.map((s) => (
                          <Tooltip key={s.id} title={s.description} arrow>
                            <Chip
                              label={s.name}
                              size="small"
                              sx={{
                                bgcolor: "rgba(192, 132, 252, 0.2)",
                                borderColor: "rgba(192, 132, 252, 0.4)",
                              }}
                              variant="outlined"
                            />
                          </Tooltip>
                        ))}
                      </Stack>
                    </>
                  )}
                </CardContent>
              </AnimatedCard>
            </motion.div>

            {/* Narrator Thoughts (debug) */}
            {thoughtsQuery.data && thoughtsQuery.data.length > 0 && (
              <motion.div variants={fadeInUp}>
                <AnimatedCard sx={{ mt: 2 }} disableHover delay={0.3}>
                  <CardContent>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Narrator Thoughts
                    </Typography>
                    <Stack spacing={1}>
                      {thoughtsQuery.data.slice(0, 4).map((t) => (
                        <Box
                          key={t.id}
                          sx={{
                            p: 1,
                            borderRadius: 1,
                            bgcolor: "rgba(255,255,255,0.02)",
                            borderLeft: "2px solid",
                            borderColor: "primary.main",
                          }}
                        >
                          <Typography variant="body2" fontWeight={500}>
                            {t.plan}
                          </Typography>
                          <Typography
                            variant="caption"
                            color="text.secondary"
                            sx={{ fontStyle: "italic" }}
                          >
                            {t.thought}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  </CardContent>
                </AnimatedCard>
              </motion.div>
            )}
          </Grid>
        </Grid>
      </Stack>
    </motion.div>
  );
}
