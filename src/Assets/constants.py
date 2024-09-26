### Program/GUI
YES_OPTIONS = {"y", "yes", "on", "1", "yeah", "true", "sure", "yup",
               "ja", "si", "sí", "haan", "हाँ", "oui", "はい", "da"}
WARP_OPTIONS = {"blue", "b", "warped", "w", "warp"}
CRMS_OPTIONS = {"red", "r", "crimson", "c", "crim"}
BASE_CPU_ITER_TIME = 5.5e-4
WARPED = 0
CRIMSON = 1

# def get_dpi_scale_factor():
#     """Get the resolution scale factor based on monitor DPI."""
#     try:
#         # Set process DPI awareness (for newer versions of Windows)
#         windll.shcore.SetProcessDpiAwareness(1)
        
#         # Obtain the monitor handle for the primary monitor
#         hdc = windll.user32.GetDC(0)
        
#         # Get the DPI (LOGPIXELSX = 88)
#         dpi = windll.gdi32.GetDeviceCaps(hdc, 88)
        
#         # Release the device context handle
#         windll.user32.ReleaseDC(0, hdc)

#         # Standard DPI is 96, calculate the scale factor based on this
#         return 1.25
#         return dpi / 96.0
#     except:
#         return 1.25  # Default fallback

# # Resolution Scale Factor
# RSF = get_dpi_scale_factor() if windll else 1.25  # Automatically set based on DPI
# Lets just chill with aint any scaling for now shall we?
RSF = 1

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
FOLIAGE_COLLECTION_EFFIC = 0.825 # Takes into account avg effic and des fungi aren't accounted for

### Small Fungi
FUNG_GROWTH_CHANCE = 0.4
AVG_BM_TO_GROW_FUNG = 1 / FUNG_GROWTH_CHANCE
FUNG_SPREAD_RAD = 3
FUNG_SPREAD_DIA = 5
CRMS_FUNG_CHANCE = 11 / 99
WARP_FUNG_CHANCE = 13 / 100
