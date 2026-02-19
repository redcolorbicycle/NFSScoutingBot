# Asset file paths. Each value is a list so send_asset can use random.choice uniformly.
ASSETS = {
    "cmboost":           ["assets/cmtable.jpg"],
    "trainers":          ["assets/trainers.jpg"],
    "fivetoolboost":     ["assets/fivetooltable.jpg"],
    "respondtostevie":   ["assets/steviegif.mp4"],
    "wtf":               ["assets/wtf.jpg"],
    "respondtostevie2":  ["assets/stare.gif"],
    "hehe":              ["assets/run.gif"],
    "stevie":            ["assets/stevielose.jpg"],
    "ohno":              ["assets/shock.jpg"],
    "boom":              ["assets/boom.gif", "assets/boom2.gif", "assets/boom3.gif"],
    "cyclopssweep":      ["assets/cyclopssweep.gif"],
    "sweep":             ["assets/sweep1.gif", "assets/sweep2.gif", "assets/sweep3.gif"],
    "click":             ["assets/images.mp4"],
    "kiss":              ["assets/catkiss.gif"],
    "cupcake":           ["assets/cupcake1.gif", "assets/cupcake2.gif"],
    "fuckyou":           ["assets/gnome.gif"],
    "cursed":            ["assets/cursed.gif"],
    "goldskilltrainers": ["assets/goldskilltrainers.jpg"],
    "five":              ["assets/five.gif"],
    "jfc":               ["assets/jfc.jpg"],
    "pcoboost":          ["assets/PCO.jpg"],
    "flag":              ["assets/flag.jpg"],
    "mrpboost":          ["assets/MrPerfect.jpg"],
    "shame":             ["assets/shame.gif"],
}

# PR color thresholds: (max_value_inclusive, hex_color)
PR_COLORS = [
    (50,   "#FF0000"),  # top 50: red
    (200,  "#FFA500"),  # 51–200: orange
    (500,  "#FFFF00"),  # 201–500: yellow
    (1000, "#ADD8E6"),  # 501–1000: light blue
    (2000, "#D397F8"),  # 1001–2000: purple
]

# Roles allowed to run player/club management commands
LEADERSHIP_ROLES = [
    "TooDank Leaders", "Vice", "NFS Ops", "NFS OG Leaders",
    "NeedForSpeed Leaders", "M16Speed Spy Daddies", "GoldyLeads", "Burnout Leaders",
    "Dugout Leads", "Kerchoo Leaders", "Rush Hour Leaders", "Speed Bump Leaders",
    "ImOnSpeed Leaders", "NFS_NoLimits Leaders", "Scout Squad", "M16 Recruit", "TooDankFast",
]

# Roles allowed to run battle log commands
BATTLE_LOG_ROLES = [
    "TooDank Leaders", "Vice", "TokyoDrift Leaders", "NFS Ops", "NFS OG Leaders",
    "NeedForSpeed Leaders", "M16Speed Spy Daddies", "GoldyLeads", "Burnout Leaders",
    "Dugout Leads", "Kerchoo Leaders", "Rush Hour Leaders", "Speed Bump Leaders",
    "ImOnSpeed Leaders", "NFS_NoLimits Leaders", "Scout Squad",
]

# Discord user IDs allowed to use batting/pitching stat analysis commands
ALLOWED_ANALYST_IDS = {
    355004588186796035, 327567846567575554, 249243533246988292,
    1209287557121318974, 635463073712570385, 237066640448159746,
    460950294893690880, 1231605248041156653, 698184128478314566,
    958512461500276736, 629122681261785118, 143909682237538304,
    1145543271330881599, 1091901514848678061, 536258698461577236,
    1042374780550135868, 200767106453733386, 617029165597720592,
    308760445160783882, 788709027570778123, 789922571834884107,
    1062838877527756980, 812515320664162324, 703051352141725810,
    807822868020199435, 1150787076581752913, 1155995827102302218,
    911330343741702194, 693621768853782569, 976439679903748096,
    114602366652776450,
}

# Default number of rows per paginated table
ROWS_PER_PAGE = 30

# Five-tool calculator constants
FIVETOOL_BONUSES = [110, 108, 105, 103, 100, 98, 95, 93, 90, 88]
FIVETOOL_TRAINING_NORMAL = 57
FIVETOOL_TRAINING_SUPREME = 87

# Excel template file paths
UPLOAD_TEMPLATE = "uploadtemplate.xlsx"
BATTLE_LOG_TEMPLATE = "battlelogs.xlsx"
