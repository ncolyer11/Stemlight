### Program/GUI
YES_OPTIONS = {"y", "yes", "on", "1", "yeah", "true", "sure", "yup",
               "ja", "si", "sí", "haan", "हाँ", "oui", "はい", "da"}
WARP_OPTIONS = {"blue", "b", "warped", "w", "warp"}
CRMS_OPTIONS = {"red", "r", "crimson", "c", "crim"}
# Resoloution Scale Factor
RSF = 1.25 # Lower for Linux and MacOS, but changes to 1.5 on Windows to fix dpi scaling
try:
    from ctypes import windll
    RSF = 1.5
except ImportError:
    pass

### Minecraft
TICKS_PER_HR = 72000
DSPNR_CLDWN = 4

### Huge Fungi Growth
NT_MAX_RAD = 3
NT_MAX_HT = 27
NT_MAX_WD = 7
TRUNK_DIST = 7 * [0, 1 / 120] + 3 * [11 / 120, 12 / 120] + 4 * [11 / 120] + 3 * [0.0]
CUML_TRUNK_DIST = [0.0] * (len(TRUNK_DIST) + 1)
for index in range(1, len(TRUNK_DIST)):
    CUML_TRUNK_DIST[index] = (CUML_TRUNK_DIST[index - 1] + TRUNK_DIST[index])
CUML_TRUNK_DIST = CUML_TRUNK_DIST[NT_MAX_HT - 1::-1]

### Huge Fungi Farming
WARTS_PER_BM = 137 / 17
FOLIAGE_PER_BM = 133 / 13
BM_FOR_CRMS_FUNG = (TICKS_PER_HR / DSPNR_CLDWN - 11423) / 14608
AVG_STEMS = 221 / 24
AVG_SHROOMS = 2.03192455026454
AVG_WARTS = 63.0252319962964
AVG_TOP_WART = 0.97951
BLOCK_TYPES = ["Stems", "Shroomlights", "Wart Blocks (VRM 0)"]

### Small Fungi
FUNG_GROWTH_CHANCE = 0.4
AVG_BM_TO_GROW_FUNG = 1 / FUNG_GROWTH_CHANCE
FUNG_SPREAD_RAD = 3
FUNG_SPREAD_DIA = 5
CRMS_FUNG_CHANCE = 11 / 99
WARP_FUNG_CHANCE = 13 / 100
