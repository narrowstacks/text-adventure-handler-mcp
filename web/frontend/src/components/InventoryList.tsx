import { useState } from "react";
import {
  Card,
  CardContent,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemButton,
  Box,
  Chip,
  Stack,
  Dialog,
  DialogTitle,
  DialogContent,
  IconButton,
  Divider,
} from "@mui/material";
import type { InventoryItem } from "../types";
import BackpackIcon from "@mui/icons-material/Backpack";
import CloseIcon from "@mui/icons-material/Close";

interface InventoryListProps {
  inventory: InventoryItem[];
}

const capitalize = (str: string): string => {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1);
};

export default function InventoryList({ inventory }: InventoryListProps) {
  const [selectedItem, setSelectedItem] = useState<InventoryItem | null>(null);

  const handleItemClick = (item: InventoryItem) => {
    setSelectedItem(item);
  };

  const handleClose = () => {
    setSelectedItem(null);
  };

  return (
    <>
      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Box sx={{ display: "flex", alignItems: "center", mb: 1 }}>
            <BackpackIcon color="primary" sx={{ mr: 1 }} />
            <Typography variant="h6">Inventory</Typography>
          </Box>
          {inventory.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              Empty
            </Typography>
          ) : (
            <List dense disablePadding>
              {inventory.map((item) => (
                <ListItem
                  key={item.id || item.name}
                  disablePadding
                  sx={{ mb: 0.5 }}
                >
                  <ListItemButton
                    onClick={() => handleItemClick(item)}
                    sx={{
                      py: 0.75,
                      px: 1.5,
                      bgcolor: "rgba(255,255,255,0.03)",
                      borderRadius: 1,
                      border: "1px solid rgba(255,255,255,0.05)",
                      "&:hover": {
                        bgcolor: "rgba(255,255,255,0.08)",
                        borderColor: "primary.main",
                      },
                    }}
                  >
                    <ListItemText
                      primary={`${item.name}${
                        item.quantity > 1 ? ` (x${item.quantity})` : ""
                      }`}
                      slotProps={{
                        primary: {
                          sx: { fontWeight: 500, fontSize: "0.9rem" },
                        },
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              ))}
            </List>
          )}
        </CardContent>
      </Card>

      <Dialog
        open={selectedItem !== null}
        onClose={handleClose}
        maxWidth="sm"
        fullWidth
        slotProps={{
          paper: {
            sx: {
              bgcolor: "background.paper",
              backgroundImage: "none",
            },
          },
          backdrop: {
            sx: {
              backdropFilter: "blur(4px)",
              backgroundColor: "rgba(0, 0, 0, 0.7)",
            },
          },
        }}
      >
        {selectedItem && (
          <>
            <DialogTitle
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                pb: 1,
              }}
            >
              <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
                <Typography variant="h6" component="span">
                  {selectedItem.name}
                </Typography>
                {selectedItem.quantity > 1 && (
                  <Chip
                    label={`x${selectedItem.quantity}`}
                    size="small"
                    color="primary"
                  />
                )}
              </Box>
              <IconButton onClick={handleClose} size="small">
                <CloseIcon />
              </IconButton>
            </DialogTitle>
            <DialogContent>
              {selectedItem.description && (
                <Typography variant="body1" sx={{ mb: 2 }}>
                  {selectedItem.description}
                </Typography>
              )}

              {selectedItem.properties &&
                Object.keys(selectedItem.properties).length > 0 && (
                  <>
                    <Divider sx={{ my: 2 }} />
                    <Typography
                      variant="subtitle2"
                      color="text.secondary"
                      sx={{ mb: 1 }}
                    >
                      Properties
                    </Typography>
                    <Stack spacing={1}>
                      {Object.entries(selectedItem.properties).map(
                        ([key, value]) => {
                          const strValue = String(value);
                          const isLongValue = strValue.length > 30;

                          return (
                            <Box
                              key={key}
                              sx={{
                                display: "flex",
                                flexDirection: isLongValue ? "column" : "row",
                                justifyContent: isLongValue
                                  ? "flex-start"
                                  : "space-between",
                                alignItems: isLongValue
                                  ? "flex-start"
                                  : "center",
                                gap: isLongValue ? 0.5 : 0,
                                py: 0.75,
                                px: 1.5,
                                bgcolor: "rgba(255,255,255,0.03)",
                                borderRadius: 1,
                              }}
                            >
                              <Typography
                                variant="body2"
                                color="text.secondary"
                                sx={{ flexShrink: 0 }}
                              >
                                {capitalize(key)}
                              </Typography>
                              <Typography
                                variant="body2"
                                fontWeight={500}
                                sx={{
                                  textAlign: isLongValue ? "left" : "right",
                                  wordBreak: "break-word",
                                }}
                              >
                                {capitalize(strValue)}
                              </Typography>
                            </Box>
                          );
                        }
                      )}
                    </Stack>
                  </>
                )}
            </DialogContent>
          </>
        )}
      </Dialog>
    </>
  );
}
