import { useQuery } from "@tanstack/react-query";
import Grid from "@mui/material/GridLegacy";
import {
  Card,
  CardContent,
  Typography,
  Box,
  Stack,
  Chip,
  LinearProgress,
  Divider,
} from "@mui/material";
import { motion } from "framer-motion";
import PlayArrowRounded from "@mui/icons-material/PlayArrowRounded";
import HistoryIcon from "@mui/icons-material/History";
import AutoGraphIcon from "@mui/icons-material/AutoGraph";
import SparklesIcon from "@mui/icons-material/AutoAwesome";
import FavoriteIcon from "@mui/icons-material/Favorite";
import { useNavigate } from "react-router-dom";
import { getAdventures, getDashboard, getSessions } from "../api";
import { AnimatedCard } from "../components/AnimatedCard";
import { SessionCardSkeleton, CardSkeleton } from "../components/Skeletons";
import { staggerContainer, fadeInUp, useReducedMotion } from "../utils/animations";

export default function Home() {
  const navigate = useNavigate();
  const reducedMotion = useReducedMotion();
  const { data: dashboard } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboard,
  });
  const { data: sessions, isLoading: sessionsLoading } = useQuery({
    queryKey: ["sessions"],
    queryFn: () => getSessions(24),
  });
  const { data: adventures, isLoading: adventuresLoading } = useQuery({
    queryKey: ["adventures"],
    queryFn: getAdventures,
  });

  if (sessionsLoading || adventuresLoading) {
    return (
      <Stack spacing={4}>
        <Grid container spacing={2}>
          {[1, 2, 3].map((i) => (
            <Grid item xs={12} md={4} key={i}>
              <CardSkeleton />
            </Grid>
          ))}
        </Grid>
        <Card>
          <CardContent>
            <Grid container spacing={2}>
              {[1, 2, 3].map((i) => (
                <Grid item xs={12} md={6} lg={4} key={i}>
                  <SessionCardSkeleton />
                </Grid>
              ))}
            </Grid>
          </CardContent>
        </Card>
      </Stack>
    );
  }

  return (
    <motion.div
      initial={reducedMotion ? false : "hidden"}
      animate="visible"
      variants={staggerContainer}
    >
      <Stack spacing={4}>
        <motion.div variants={fadeInUp}>
          <Box
            sx={{ display: "flex", flexWrap: "wrap", alignItems: "center", gap: 2 }}
          >
            <motion.div
              animate={reducedMotion ? {} : { rotate: [0, 10, -10, 0] }}
              transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
            >
              <SparklesIcon color="secondary" sx={{ fontSize: 32 }} />
            </motion.div>
            <Box>
              <Typography
                variant="overline"
                sx={{ letterSpacing: 1.5, opacity: 0.7 }}
              >
                Live MCP Data
              </Typography>
              <Typography variant="h3">Adventure Control Room</Typography>
              <Typography variant="body1" sx={{ maxWidth: 720, opacity: 0.75 }}>
                Monitor every running session, peek into worlds, and keep the MCP
                database in sync with a deliberate, human-friendly console.
              </Typography>
            </Box>
          </Box>
        </motion.div>

        <Grid container spacing={2}>
          <Grid item xs={12} md={4}>
            <motion.div variants={fadeInUp}>
              <AnimatedCard delay={0.1} glowColor="rgba(124, 231, 194, 0.2)">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Active Sessions
                  </Typography>
                  <Typography variant="h3" sx={{ mb: 1, color: "primary.main" }}>
                    {dashboard?.active_sessions ?? 0}
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={Math.min((dashboard?.active_sessions ?? 0) * 10, 100)}
                    sx={{
                      height: 6,
                      borderRadius: 3,
                      bgcolor: "rgba(255,255,255,0.1)",
                    }}
                  />
                </CardContent>
              </AnimatedCard>
            </motion.div>
          </Grid>
          <Grid item xs={12} md={4}>
            <motion.div variants={fadeInUp}>
              <AnimatedCard delay={0.2} glowColor="rgba(255, 139, 167, 0.2)">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Total Adventures
                  </Typography>
                  <Typography variant="h3" sx={{ mb: 1, color: "secondary.main" }}>
                    {dashboard?.totals.adventures ?? 0}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Templates available to start new stories
                  </Typography>
                </CardContent>
              </AnimatedCard>
            </motion.div>
          </Grid>
          <Grid item xs={12} md={4}>
            <motion.div variants={fadeInUp}>
              <AnimatedCard delay={0.3} glowColor="rgba(240, 199, 94, 0.2)">
                <CardContent>
                  <Typography variant="subtitle2" color="text.secondary">
                    Crowd Favorite
                  </Typography>
                  <Typography variant="h5" sx={{ mb: 0.5 }}>
                    {dashboard?.top_adventure?.title ?? "No plays yet"}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {dashboard?.top_adventure
                      ? `${dashboard.top_adventure.plays} sessions`
                      : "Play a session to see stats"}
                  </Typography>
                </CardContent>
              </AnimatedCard>
            </motion.div>
          </Grid>
        </Grid>

        <motion.div variants={fadeInUp}>
          <AnimatedCard disableHover>
            <CardContent>
              <Stack direction="row" alignItems="center" spacing={1} sx={{ mb: 2 }}>
                <PlayArrowRounded color="primary" />
                <Typography variant="h6">Latest Sessions</Typography>
              </Stack>
              <Grid container spacing={2}>
                {sessions?.map((session, index) => {
                  const hp = session.hp ?? 0;
                  const maxHp = session.max_hp ?? 1;
                  const currency = session.currency ?? 0;
                  const hpPercent = Math.round((hp / maxHp) * 100);
                  const hpColor =
                    hpPercent > 60 ? "#7ce7c2" : hpPercent > 30 ? "#f0c75e" : "#ff6b6b";

                  return (
                    <Grid item xs={12} md={6} lg={4} key={session.id}>
                      <motion.div
                        initial={reducedMotion ? {} : { opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                        whileHover={reducedMotion ? {} : { y: -4, scale: 1.01 }}
                      >
                        <Card
                          variant="outlined"
                          onClick={() => navigate(`/session/${session.id}`)}
                          sx={{
                            cursor: "pointer",
                            height: "100%",
                            borderColor: "rgba(255,255,255,0.08)",
                            transition: "all 0.2s ease",
                            "&:hover": {
                              borderColor: "secondary.main",
                              boxShadow: "0 10px 40px rgba(0,0,0,0.3)",
                            },
                          }}
                        >
                          <CardContent>
                            <Stack
                              direction="row"
                              justifyContent="space-between"
                              alignItems="center"
                              mb={1}
                            >
                              <Typography variant="overline" color="text.secondary">
                                {new Date(session.last_played).toLocaleString()}
                              </Typography>
                              <Stack direction="row" alignItems="center" spacing={0.5}>
                                <FavoriteIcon sx={{ fontSize: 14, color: hpColor }} />
                                <Typography
                                  variant="caption"
                                  sx={{ color: hpColor, fontWeight: 600 }}
                                >
                                  {hp}/{maxHp}
                                </Typography>
                              </Stack>
                            </Stack>
                            <Typography variant="h5" sx={{ mb: 1 }}>
                              {session.adventure_title || "Unknown Adventure"}
                            </Typography>
                            <Stack
                              direction="row"
                              spacing={1}
                              sx={{ mb: 1 }}
                              alignItems="center"
                              flexWrap="wrap"
                              useFlexGap
                            >
                              <Chip
                                size="small"
                                label={session.location}
                                color="secondary"
                                sx={{ maxWidth: 150, "& .MuiChip-label": { overflow: "hidden", textOverflow: "ellipsis" } }}
                              />
                              <Chip
                                size="small"
                                label={`Score ${session.score ?? 0}`}
                                variant="outlined"
                                sx={{ bgcolor: "rgba(124, 231, 194, 0.1)" }}
                              />
                              {currency > 0 && (
                                <Chip
                                  size="small"
                                  label={`${currency} gold`}
                                  variant="outlined"
                                  sx={{ bgcolor: "rgba(240, 199, 94, 0.1)" }}
                                />
                              )}
                            </Stack>
                            <Stack direction="row" spacing={2} alignItems="center">
                              <HistoryIcon fontSize="small" color="disabled" />
                              <Typography variant="body2" color="text.secondary">
                                Day {session.game_day ?? 1} •{" "}
                                {String(session.game_time ?? 0).padStart(2, "0")}:00h
                              </Typography>
                            </Stack>
                          </CardContent>
                        </Card>
                      </motion.div>
                    </Grid>
                  );
                })}
              </Grid>
            </CardContent>
          </AnimatedCard>
        </motion.div>

        <motion.div variants={fadeInUp}>
          <AnimatedCard disableHover>
            <CardContent>
              <Stack direction="row" spacing={1} alignItems="center" sx={{ mb: 2 }}>
                <AutoGraphIcon color="secondary" />
                <Typography variant="h6">Adventure Templates</Typography>
              </Stack>
              <Grid container spacing={2}>
                {adventures?.map((adv, index) => (
                  <Grid item xs={12} md={6} lg={4} key={adv.id}>
                    <motion.div
                      initial={reducedMotion ? {} : { opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      transition={{ delay: index * 0.05 }}
                      whileHover={reducedMotion ? {} : { scale: 1.02 }}
                    >
                      <Card
                        variant="outlined"
                        sx={{
                          height: "100%",
                          transition: "all 0.2s ease",
                          "&:hover": {
                            borderColor: "primary.main",
                            boxShadow: "0 0 20px rgba(124, 231, 194, 0.2)",
                          },
                        }}
                      >
                        <CardContent>
                          <Typography variant="overline" color="text.secondary">
                            {adv.id}
                          </Typography>
                          <Typography variant="h5" sx={{ mb: 1 }}>
                            {adv.title}
                          </Typography>
                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{ mb: 1.5, minHeight: 40 }}
                          >
                            {adv.description}
                          </Typography>
                          <Divider sx={{ my: 1 }} />
                          <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                            {adv.stats.slice(0, 4).map((s) => (
                              <Chip
                                key={s.name}
                                size="small"
                                label={`${s.name}: ${s.default_value}`}
                                sx={{
                                  fontSize: "0.7rem",
                                  height: 22,
                                  bgcolor: "rgba(124, 231, 194, 0.1)",
                                  borderColor: "rgba(124, 231, 194, 0.3)",
                                }}
                                variant="outlined"
                              />
                            ))}
                            {adv.stats.length > 4 && (
                              <Chip
                                size="small"
                                label={`+${adv.stats.length - 4} more`}
                                sx={{
                                  fontSize: "0.7rem",
                                  height: 22,
                                  bgcolor: "rgba(255,255,255,0.05)",
                                }}
                              />
                            )}
                          </Stack>
                        </CardContent>
                      </Card>
                    </motion.div>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </AnimatedCard>
        </motion.div>
      </Stack>
    </motion.div>
  );
}
