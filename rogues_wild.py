#!/usr/bin/env python3
"""
ROGUES WILD — a gentle folklore roguelike.

No win condition. No quest log. Just hills, herbs, and creatures
with something to say. Standard library only.

    python3 rogues_wild.py
"""

import random
import shutil
import sys

try:
    import termios
    import tty
    HAVE_TERMIOS = True
except ImportError:
    HAVE_TERMIOS = False

# ---------------------------------------------------------------- terminal

RESET = "\x1b[0m"
CLEAR = "\x1b[H\x1b[2J"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"


def col(code, text):
    if not code:
        return text
    return "\x1b[%sm%s%s" % (code, text, RESET)


def read_key():
    """Read one keypress. Arrow keys are translated to h/j/k/l."""
    if not HAVE_TERMIOS or not sys.stdin.isatty():
        line = sys.stdin.readline()
        if not line:
            return "Q"
        return line[0] if line.strip() else " "
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setcbreak(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            ch2 = sys.stdin.read(1)
            if ch2 == "[":
                ch3 = sys.stdin.read(1)
                return {"A": "k", "B": "j", "C": "l", "D": "h"}.get(ch3, "\x1b")
            return "\x1b"
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


# ---------------------------------------------------------------- tiles

# glyph: (description, passable, color)
TILES = {
    ".": ("soft turf", True, "90"),
    ",": ("tall grass", True, "32"),
    "&": ("an old tree", False, "32"),
    "^": ("steep crags", False, "37"),
    "~": ("dark water", False, "34"),
    "=": ("worn planks", True, "33"),
    "#": ("a wall", False, "37"),
    "+": ("a door", True, "93"),
    "o": ("a cave mouth", True, "90"),
    "O": ("the Great Gate", True, "93"),
    ">": ("a stair spiralling down", True, "93"),
    "<": ("a stair climbing up", True, "93"),
    "*": ("a crackling campfire", False, "91"),
    " ": ("nothing", False, ""),
}

DIRS = {"h": (-1, 0), "l": (1, 0), "k": (0, -1), "j": (0, 1)}

# ---------------------------------------------------------------- items

# key: (name, glyph, kind, power, color, description)
ITEM_DEFS = {
    # herbs ------------------------------------------------------------
    "kingsfoil": ("sprig of kingsfoil", '"', "herb", 6, "92",
                  "A healer's weed. Smells like clean rain."),
    "moonpetal": ("moonpetal", '"', "herb", 0, "95",
                  "Pale and cool. It remembers moonlight for you."),
    "bittermoss": ("clump of bittermoss", '"', "herb", 2, "92",
                   "Good for the knees, says everyone's grandmother."),
    "dreamleaf": ("dreamleaf", '"', "herb", 1, "92",
                  "Chewing it makes the clouds look back."),
    "glowcap": ("glowcap mushroom", '"', "herb", 0, "96",
                "A mushroom with its own opinion of the dark."),
    # food ---------------------------------------------------------------
    "seedcake": ("seedcake", "%", "food", 4, "33", "Dense, honest, hobbit-made."),
    "pancake": ("pancake with jam", "%", "food", 5, "33", "Still warm, somehow."),
    "jam": ("jar of Mamma's jam", "%", "food", 7, "33", "Plum, mostly. Summer, partly."),
    "bilberries": ("handful of dried bilberries", "%", "food", 3, "33",
                   "Forage from a good late-summer week."),
    "picnic": ("fat wicker picnic-basket", "%", "food", 6, "33",
               "coldchickencoldtonguecoldhampickledgherkinssaladfrenchrolls"
               "cresssandwiches — and, somewhere at the bottom, gingerbeer."),
    # weapons (such as they are) ------------------------------------------
    "walkingstick": ("walking stick", ")", "weapon", 1, "37",
                     "It has done a great many miles and complains about none of them."),
    "oakstaff": ("oaken staff", ")", "weapon", 1, "37",
                 "Apprentice-issue. The wizard's initials are burned near the top."),
    "hornknife": ("horn-handled knife", ")", "weapon", 2, "37",
                  "For bread, kindling, and very last resorts."),
    "ladle": ("Mamma's ladle", ")", "weapon", 1, "37",
              "Heavier than it looks. Mamma never needed anything else."),
    "hazelwand": ("hazel wand", ")", "weapon", 1, "95",
                  "It hums faintly near water and complains near iron."),
    "broom": ("birch-twig broom", ")", "weapon", 1, "33",
              "Good for sweeping, shooing, and — one day, perhaps — flying."),
    "oar": ("worn sculling oar", ")", "weapon", 2, "33",
            "Smooth-handled from a thousand quiet mornings on the river. "
            "There is nothing, absolutely nothing, half so much worth doing."),
    "dragonsword": ("dragon-slaying sword", ")", "weapon", 12, "96",
                    "Forged by the ancients of the West to end the worm under the "
                    "mountain. Its edge remembers cold fire, and one purpose only."),
    # wearables ----------------------------------------------------------
    "greenhood": ("green hood", "[", "cloak", 1, "32",
                  "Forest-colored. Rain runs off it like an argument."),
    "patchrobe": ("patched robe", "[", "cloak", 1, "36",
                  "Each patch is a lesson. There are many patches."),
    "scarf": ("woolly scarf", "[", "cloak", 1, "36",
              "Knitted by Moominmamma. Adventures are mostly weather."),
    "waistcoat": ("brass-buttoned waistcoat", "[", "cloak", 1, "33",
                  "Respectable. The buttons are polished every Sunday."),
    "boatcoat": ("blue boating-coat", "[", "cloak", 1, "34",
                 "River-blue and river-fond. The pockets keep turning up "
                 "string, and a bit of bread, and one perfect flat stone."),
    "eldercloak": ("cloak of elder-leaves", "[", "cloak", 2, "32",
                   "Woven from leaves that never agreed to fall."),
    "pointyhat": ("pointy black hat", "[", "cloak", 1, "90",
                  "Wide of brim and sure of itself. A hat with prospects."),
    # light ----------------------------------------------------------------
    "lantern": ("tin lantern", "{", "light", 4, "93",
                "A candle stub inside. It keeps the dark polite."),
    # fishing --------------------------------------------------------------
    "fishingrod": ("willow fishing rod", "/", "rod", 0, "33",
                   "A patient sort of tool. The water end does most of the work."),
    "perch": ("striped perch", "%", "food", 3, "36",
              "Stripes like reeds. It looks faintly indignant."),
    "pike": ("young pike", "%", "food", 5, "36",
             "All teeth and opinions, like its elders."),
    "bream": ("bronze bream", "%", "food", 4, "33",
              "Flat, calm, and resigned to everything."),
    "trout": ("speckled trout", "%", "food", 5, "36",
              "Cold-water quick. The speckles are very fine work."),
    "vendace": ("silvery vendace", "%", "food", 2, "37",
                "Small, bright, and best in great company."),
    "eel": ("bewildered eel", "%", "food", 4, "90",
            "It has clearly taken a wrong turn somewhere."),
    "ruffe": ("grumpy little ruffe", "%", "food", 2, "90",
              "Mostly spines and grievance. Still, a catch is a catch."),
    # scrolls ----------------------------------------------------------------
    "scroll_glimmer": ("weathered scroll of GLIMMER", "?", "scroll", 0, "95",
                       "A charm of small light, copied in a careful hand."),
    "scroll_ember": ("singed scroll of EMBERKINDLE", "?", "scroll", 0, "95",
                     "A charm of small fire. The margins are full of apologies."),
    "scroll_hush": ("soft grey scroll of HUSHWORD", "?", "scroll", 0, "95",
                    "A charm for calming what you should not have angered."),
    # recipes ----------------------------------------------------------------
    "recipe_heal": ("stained recipe for HEALING DRAUGHT", "?", "recipe", 0, "92",
                    "The bog-witch's hand. 'Kingsfoil for the hurt, bittermoss "
                    "for the knees, and don't let it boil over.'"),
    "recipe_moon": ("silvery recipe for MOONLIGHT CORDIAL", "?", "recipe", 0, "95",
                    "Written in ink that catches the light. 'Moonpetal and "
                    "glowcap, steeped cold, drunk colder.'"),
    "recipe_dream": ("crumpled recipe for DREAM TEA", "?", "recipe", 0, "96",
                     "'Dreamleaf and moonpetal. Pour for anyone who is being "
                     "difficult, yourself included.'"),
    # brews ------------------------------------------------------------------
    "potion_heal": ("flask of healing draught", "!", "potion", 8, "92",
                    "Green-gold and warm to hold. It smells of clean rain "
                    "and somebody's kitchen."),
    "potion_moon": ("phial of moonlight cordial", "!", "potion", 0, "95",
                    "Pale and cool, faintly glowing. The dark gives it room."),
    "potion_dream": ("cup of dream tea", "!", "potion", 0, "96",
                     "Still steaming. It smells like an afternoon with "
                     "nothing in it."),
    # curios -----------------------------------------------------------------
    "pearl": ("river pearl", "!", "curio", 0, "96",
              "The river made this and then forgot about it."),
    "kettle": ("old copper kettle", "!", "curio", 0, "33",
               "Somebody's best kettle, once. It could be again."),
    "helm": ("knight's rusted helm", "!", "curio", 0, "37",
             "Whoever wore it had a very hard day, very long ago."),
    "coin": ("ancient gold coin", "!", "curio", 0, "93",
             "The king on it has been forgotten by everyone but the coin."),
    "stone": ("smooth grey stone", "!", "curio", 0, "37",
              "An extremely good stone. You can tell."),
    "dragonheart": ("the dragon's heart", "!", "curio", 0, "91",
                    "Warm. It beats, faintly. ...Now what?"),
    "silmaril": ("a Silmaril", "*", "curio", 0, "1;97",
                 "A holy jewel, and in it the light of two trees that died "
                 "before the moon was made. It is cool, and it is not sorry "
                 "for anything it has cost."),
}

SCROLL_SPELL = {
    "scroll_glimmer": "glimmer",
    "scroll_ember": "emberkindle",
    "scroll_hush": "hushword",
}

SPELLS = {
    # name: (mp cost, blurb)
    "glimmer": (1, "a small light that follows you a while"),
    "emberkindle": (2, "a spark thrown at an arm's length"),
    "hushword": (1, "a word that settles ruffled tempers"),
}

RECIPE_SCROLL = {
    "recipe_heal": "healing draught",
    "recipe_moon": "moonlight cordial",
    "recipe_dream": "dream tea",
}

RECIPES = {
    # name: (ingredient item keys, brewed item key, blurb)
    "healing draught": (("kingsfoil", "bittermoss"), "potion_heal",
                        "mends what aches, all at once"),
    "moonlight cordial": (("moonpetal", "glowcap"), "potion_moon",
                          "fills the well of magic and brightens the dark"),
    "dream tea": (("dreamleaf", "moonpetal"), "potion_dream",
                  "settles every ruffled temper within earshot"),
}

# fish that might live in this particular Wild; each game stocks only a few
FISH_KEYS = ["perch", "pike", "bream", "trout", "vendace", "eel", "ruffe"]
FISH_CHANCE = 0.35

FISHING_MISSES = [
    "The float bobs once, considers, and thinks better of it.",
    "Something nibbles, takes your measure, and declines.",
    "You catch a fine long strand of waterweed. The lake's idea of a joke.",
    "The line drifts. The clouds drift. Nothing else commits to anything.",
    "A swirl, a flash of silver — gone. The water keeps its own counsel.",
]


class Item:
    def __init__(self, key):
        name, glyph, kind, power, color, desc = ITEM_DEFS[key]
        self.key = key
        self.name = name
        self.glyph = glyph
        self.kind = kind
        self.power = power
        self.color = color
        self.desc = desc


# ---------------------------------------------------------------- creatures

# key: (name, glyph, color, hp, strength, static, lines)
NPC_DEFS = {
    "fox": ("the fox", "f", "33", 4, 2, False, [
        "The fox tilts its head. 'You smell of doors,' it says, and does not explain.",
        "'The raven lies,' says the fox. 'But beautifully.'",
        "'If you ever find a golden feather, leave it be. That's my advice, freely given.'",
    ]),
    "raven": ("the raven", "r", "90", 3, 1, False, [
        "'KRRA. The dragon under the mountain owes me a button,' says the raven. "
        "'Go take its heart, and fetch my button while you're in there!'",
        "'I have seen your roof,' says the raven, meaningfully.",
        "'Shiny things end up where they wish to be. I merely help them along.'",
    ]),
    "deer": ("the deer", "d", "33", 5, 1, False, [
        "The deer watches you for a long, calm moment, then returns to its grazing.",
        "'The wolves keep the old law,' the deer says softly. 'Walk loud, friend.'",
    ]),
    "hedgehog": ("the hedgehog", "h", "33", 2, 1, False, [
        "'Mind the feet, mind the feet,' mutters the hedgehog.",
        "'A saucer of milk would not go amiss. Just saying. Just saying.'",
    ]),
    "squirrel": ("the squirrel", "q", "33", 2, 1, False, [
        "'I buried something important here. Or there. Possibly elsewhere,' says the squirrel.",
        "'Winter's a rumor till it isn't!' the squirrel declares, and spirals up a trunk.",
    ]),
    "wolf": ("the grey wolf", "W", "37", 12, 4, False, [
        "The wolf regards you levelly. 'The forest keeps its own law,' it says. "
        "'You are a guest in it.'",
        "'We sing at the moon because the moon never interrupts.'",
    ]),
    "tomte": ("the tomte", "t", "91", 8, 3, True, [
        "'Someone's been skipping the Yule porridge,' the tomte grumbles. "
        "'I keep accounts, you know.'",
        "'Go steal the dragon's heart!' the tomte says brightly. "
        "'Then we'd see some proper weather around here.'",
        "'Barns don't sweep themselves. Well. Mine does, but that's different.'",
    ]),
    "troll": ("the bridge troll", "T", "37", 20, 6, True, [
        "'MY bridge,' the troll rumbles, then softens. 'But you may cross. "
        "Admire the stonework as you go.'",
        "'Toll is one riddle or one kind word. You look short on riddles.'",
        "'Upstream is the wizard's business. Downstream is everyone's.'",
    ]),
    "snufkin": ("Snufkin", "S", "32", 10, 2, True, [
        "Snufkin plays five slow notes on his harmonica. "
        "'That one doesn't have a name yet,' he says.",
        "'All the paths you don't take wait politely. They're in no hurry.'",
        "'I once owned seven things. It was too many.'",
    ]),
    "fisherman": ("the old fisherman", "F", "36", 8, 2, True, [
        "'The lake takes what it likes and returns what it doesn't,' "
        "says the old fisherman. 'Mostly boots.'",
        "'There's a pike down there older than the church. We have an understanding.'",
        "'Fetch me the dragon's heart and I'll trade you my second-best hat!'",
    ]),
    "hatti": ("the hattifatteners", "i", "97", 6, 1, False, [
        "The hattifatteners sway faintly, like grass deciding something. "
        "They say nothing at all.",
        "A feeling of static and far-off thunder. "
        "The hattifatteners do not look at you, exactly.",
    ]),
    "groke": ("the Groke", "G", "94", 30, 8, False, [
        "The cold arrives before she does. The Groke looks at you with her huge dim "
        "eyes, and the ground whitens beneath her, and she says nothing at all.",
        "The Groke sighs like wind under a door. Something in you wants to sit with "
        "her, and something else wants very much to go.",
    ]),
    "wisp": ("the willow-wisp", "w", "96", 1, 1, False, [
        "'Thiiis waaay,' sings the little light, drifting toward the deep water. Best not.",
        "The wisp bobs twice, which may be a greeting or a lure.",
    ]),
    "mamma": ("Moominmamma", "M", "97", 14, 2, True, [
        "'Oh, hello dear! There's coffee on the stove, and jam in the pantry — "
        "do take some for the road.'",
        "'Remember a warm scarf. Adventures are mostly weather, you know.'",
        "Moominmamma is painting flowers on the wall. "
        "'They bloom all winter this way,' she explains.",
    ]),
    "pappa": ("Moominpappa", "P", "97", 14, 2, True, [
        "'I am at a critical chapter of my memoirs,' Moominpappa announces, "
        "clearly hoping you will ask about it.",
        "'In my day the sea was twice as deep and the storms three times as honest.'",
        "'A dragon under the mountain, you say? Splendid! Do take notes — for the memoirs.'",
    ]),
    "littlemy": ("Little My", "y", "91", 6, 3, True, [
        "'Go steal the dragon's heart!' says Little My. 'I would, but I'm busy.' "
        "She does not appear to be busy.",
        "'You walk too loud. You'll never sneak up on anything fun.'",
        "'If you meet the Groke, tell her nothing. She collects warm words and sits on them.'",
    ]),
    "tooticky": ("Too-Ticky", "u", "36", 10, 2, True, [
        "'Things are this way in winter, and that way in summer,' says Too-Ticky. "
        "'It evens out.'",
        "'The bathhouse is for thinking. The thinking is free.'",
    ]),
    "holman": ("Holman the gardener", "g", "32", 8, 2, True, [
        "'Prize-winning turnips, these, if there were prizes. "
        "Which there should be,' says Holman.",
        "'Foreign parts is anything east of the hedge, far as I'm concerned.'",
        "'A dragon's heart, baked in a pie! That'd win the fair for certain. "
        "Fetch us one, eh?'",
    ]),
    "dora": ("Aunt Dora", "a", "33", 10, 2, True, [
        "'Eat something. You're all corners,' says Aunt Dora.",
        "'Adventures. Hmph. Your grandfather went on one and came back with opinions.'",
    ]),
    "wizard": ("Maltheus the wizard", "Z", "95", 25, 6, True, [
        "'Hm? Yes, yes, the rains are three days late — I'm seeing to it,' "
        "the wizard mutters among his charts.",
        "'Magic is mostly remembering where you put things. The rest is weather.'",
        "'If you happen past the mountain, do NOT wake the dragon. Or if you do, "
        "be polite, and admire the hoard loudly.'",
        "'There is an old stair in the eastern crags that goes down past the "
        "dragon's cellar, down and down, to where a Baalrukh sleeps in fire. "
        "Kindly do not wake it. But if you must — carry something colder than "
        "its flame. The dragon's heart, say. Nothing else will do.'",
    ]),
    "witch": ("the bog-witch", "w", "92", 18, 5, True, [
        "'Come in, come in. Mind the toadstools, they're shy,' the witch says, stirring.",
        "'Bring me the dragon's heart, dearie, and I'll bake you into something "
        "marvelous. The pie, I mean. The pie.'",
        "'Glowcaps for the soup, bittermoss for the knees. Take a little, leave a little.'",
        "'My recipes? Take them, dearie, I know them all by heart. Kingsfoil "
        "and bittermoss for a healing draught — even you can't spoil that one.'",
    ]),
    "bats": ("the bats", "b", "90", 2, 1, False, [
        "A soft leathery rustle overhead. The bats discuss you briefly, "
        "then lose interest.",
    ]),
    "dragon": ("the old dragon", "D", "91", 60, 12, True, [
        "One golden eye opens, big as a shield. 'A visitor,' the dragon rumbles. "
        "'How brave. How small. Sit, if you must. Touch nothing.'",
        "'They sent you for my heart, didn't they. They always do. It is in a safe "
        "place: it beats in my chest, and there it stays.'",
        "'The wizard cheats at riddles. The witch cheats at cards. "
        "The tomte — now, the tomte I respect.'",
        "'Gold is only sunlight that learned to hold still. "
        "I keep it from wandering off.'",
    ]),
    "tombombadil": ("Tom Bombadil", "T", "93", 40, 8, True, [
        "'Hey dol! merry dol! ring a dong dillo!' Tom claps his hands. "
        "'Old Tom's the master here — of wood and water and hill. "
        "Sit, eat, be merry! No harm comes under this roof.'",
        "'The Barrow-wights are walking again, up on the downs. Cold fingers, "
        "cold hearts. Don't you let one catch you — Tom can't always come "
        "singing in time.'",
        "'A dragon, under the mountain? Ho! Tom remembers when that one was an "
        "egg, and rude even then. There's a blade laid up in the old mounds was "
        "forged to mend just such manners.'",
        "'I am the Eldest, that's what I am. I knew the river and the willow "
        "before the seas were bent. Have no fear of old grey water.'",
    ]),
    "goldberry": ("Goldberry", "G", "96", 24, 3, True, [
        "'Welcome, traveller!' laughs Goldberry, the River-woman's daughter. "
        "'The water-lilies are early this year. Come, warm your feet by the fire.'",
        "'Tom's songs keep the house safe. Out on the downs there is no singing — "
        "only the long cold sleep of the barrows. Step lightly there.'",
        "'Be at peace now, until the morning. Heed no nightly noises!'",
    ]),
    "roverandom": ("Roverandom", "d", "33", 8, 2, False, [
        "Roverandom the little dog bounces at your heels, barking for joy. "
        "He was a toy once, they say, and a moon-dog after — but he keeps "
        "that to himself.",
        "Roverandom drops a chewed stick at your feet and looks up, "
        "brimming with hope.",
        "The dog turns toward the downs, growls low in his throat, "
        "then hides behind your leg.",
    ]),
    "barrowwight": ("the Barrow-wight", "V", "96", 26, 6, False, [
        "A voice cold as old iron sighs from the dark: 'Cold be hand and heart "
        "and bone, and cold be sleep under stone...'",
    ]),
    "piper": ("the Piper", "p", "1;93", 99, 1, True, [
        "At the very edge of dawn the Piper sets his reed-pipes to his lips, "
        "and for one held breath you see Him plain — the Friend and Helper, "
        "horned and kind — and a small lost otter-cub asleep and unafraid "
        "between His hooves.",
        "The piping says, without words: 'Fear nothing. And when I am gone "
        "you shall forget, lest the memory of this great joy leave you unfit "
        "for the small good mornings that come after.'",
        "The first sunlight comes up the river like a slow gold tide. The "
        "reeds bow all together. The Piper is only reeds and wind again — "
        "but the morning is kinder than any morning you can quite remember.",
    ]),
    "robinhood": ("Robin Hood", "R", "32", 18, 5, True, [
        "'Well met, friend!' grins Robin Hood, leaning on his great longbow. "
        "'No Sheriff in these woods — only good company and a fire that asks "
        "no toll.'",
        "'Take from them as has too much, give to them as has too little. "
        "The rest is only aiming.'",
        "'Snufkin and I have an understanding: he plays, I listen, and neither "
        "of us owns a single thing worth a bailiff's trouble.'",
    ]),
    # the deep delvings — peaceful burrowing folk (level one) --------------
    "gnome": ("the gnome", "n", "33", 6, 2, False, [
        "'Mind the third tunnel, it goes nowhere but opinions,' the gnome says, "
        "tamping his little pipe.",
        "'We dig for the pleasure of the dark and the shine of what's in it — "
        "not for keeping. Never for keeping. That's how the trouble starts.'",
        "'Deeper down it stops being friendly. Deeper still, it stops being "
        "anything at all. I don't go below the second landing, and neither "
        "should you, without something cold to hold.'",
    ]),
    "badger": ("the talking badger", "e", "90", 12, 3, False, [
        "'Harrumph. Wipe your feet,' says the badger. 'This is a respectable "
        "set of tunnels, whatever the goblins two floors down would have you think.'",
        "'In my day the deep was quiet. Now there's goblins below us, orcs below "
        "them, and at the very bottom the old fire that has no business waking. "
        "I keep to my study.'",
        "'You'll want the dragon's own heart in your pocket before you go all the "
        "way down. Cold comfort against a hot sword — but comfort all the same.'",
    ]),
    "mole": ("the mole", "c", "37", 5, 1, False, [
        "'Oh! Oh my. A visitor. I do hope you're not lost,' the mole says, "
        "blinking earnestly at a patch of wall.",
        "'I dig by feel and forget by habit. Was there something I was digging "
        "toward? No matter. It'll turn up, or I will.'",
    ]),
    "shrew": ("the velvet shrew", "x", "95", 3, 1, False, [
        "'Quickquick, no time, no time,' the shrew says, and does not move at all.",
        "'Heart pounds so fast down here! Everything's an emergency. It's "
        "marvellous, really.'",
    ]),
    # the goblin warrens — hostile rabble (level two) ----------------------
    "goblin": ("the goblin", "k", "32", 8, 3, False, [
        "The goblin bares a mouthful of grievances and comes at you.",
    ]),
    "orc": ("the orc", "o", "31", 16, 5, False, [
        "The orc grunts something short and unkind, and lifts its cleaver.",
    ]),
    # the pit — the Baalrukh himself (level three) -------------------------
    "balgorg": ("Balgorg the Baalrukh", "&", "91", 80, 15, False, [
        "A pillar of shadow and flame unfolds out of the dark, and the deep "
        "grows suddenly, terribly warm. Balgorg the Baalrukh lifts a sword of "
        "living fire.",
        "'YOU CARRY A LITTLE LIGHT INTO MY DARK,' the Baalrukh rumbles, and the "
        "words fall like slag. 'I HAVE PUT OUT BRIGHTER, AND FELT NOTHING.'",
        "The flame-sword hisses as it swings. Only something older and colder "
        "than fire could stand before it.",
    ]),
    # scenery (talkable furniture; doesn't move, can't really be fought)
    "bookshelf": ("the bookshelf", "B", "33", 99, 0, True, [
        "Spines read: 'On Rains', 'Concerning Moss', 'Riddles, Vol. IX (incomplete)'.",
        "One book is shelved upside down. It seems happier that way.",
    ]),
    "cauldron": ("the cauldron", "C", "36", 99, 0, True, [
        "The cauldron simmers with something green that smells, surprisingly, wonderful.",
    ]),
    "stove": ("the kitchen stove", "C", "33", 99, 0, True, [
        "The stove is warm. There is always coffee. This is a law of the house.",
    ]),
}

SCENERY = {"bookshelf", "cauldron", "stove"}

# creatures that are hostile the moment you meet them, and stay that way
HOSTILE = {"barrowwight", "goblin", "orc", "balgorg"}


class NPC:
    def __init__(self, key, x, y):
        name, glyph, color, hp, strength, static, lines = NPC_DEFS[key]
        self.key = key
        self.name = name
        self.glyph = glyph
        self.color = color
        self.hp = hp
        self.strength = strength
        self.static = static
        self.lines = lines
        self.line_i = 0
        self.hostile = key in HOSTILE
        self.x, self.y = x, y

    def say(self):
        line = self.lines[self.line_i % len(self.lines)]
        self.line_i += 1
        return line


# ---------------------------------------------------------------- maps


class GameMap:
    def __init__(self, name, title, grid, dark=False):
        self.name = name
        self.title = title
        self.grid = grid  # list of list of tile chars
        self.h = len(grid)
        self.w = len(grid[0])
        self.dark = dark
        self.items = {}   # (x, y) -> Item
        self.npcs = []
        self.links = {}   # (x, y) -> (map name, (x, y))
        self.seen = set()

    def tile(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.grid[y][x]
        return " "

    def passable(self, x, y):
        return TILES[self.tile(x, y)][1]

    def npc_at(self, x, y):
        for n in self.npcs:
            if n.x == x and n.y == y:
                return n
        return None

    def find_open(self, x, y):
        """Nearest passable, unoccupied tile to (x, y), spiral search."""
        for r in range(0, 12):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1):
                    nx, ny = x + dx, y + dy
                    if (self.passable(nx, ny) and not self.npc_at(nx, ny)
                            and (nx, ny) not in self.links
                            and self.tile(nx, ny) not in "<>"):
                        return nx, ny
        return x, y

    def add_npc(self, key, x, y):
        x, y = self.find_open(x, y)
        self.npcs.append(NPC(key, x, y))

    def add_item(self, key, x, y):
        x, y = self.find_open(x, y)
        if (x, y) not in self.items:
            self.items[(x, y)] = Item(key)


def parse_interior(name, title, art, legend, dark=False):
    """Build a GameMap from an ASCII picture. legend maps marker chars to
    ('npc', key) / ('item', key) / ('start',). Returns (map, start, door)."""
    rows = [r for r in art.strip("\n").split("\n")]
    width = max(len(r) for r in rows)
    rows = [r.ljust(width) for r in rows]
    grid = [list(r) for r in rows]
    gmap = GameMap(name, title, grid, dark=dark)
    start = None
    door = None
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == "+":
                door = (x, y)
            if ch in legend:
                what = legend[ch]
                grid[y][x] = "."
                if what[0] == "npc":
                    gmap.npcs.append(NPC(what[1], x, y))
                elif what[0] == "item":
                    gmap.items[(x, y)] = Item(what[1])
                elif what[0] == "start":
                    start = (x, y)
    return gmap, start, door


TOWER_ART = """
###########
#B.......C#
#.........#
#....Z....#
#.........#
#.w...?...#
#....s....#
#####+#####
"""

MOOMIN_ART = """
##########
#.M....P.#
#........#
#.y..C.j.#
#...s....#
####+#####
"""

HOBBIT_ART = """
############
#.a......k.#
#..........#
#.s....{.%.#
#####+######
"""

CAVE_ART = """
##############
#....##......#
#.m..##..m...#
#....##......#
#.w.s........#
#.e..##..r...#
#....##......#
########+#####
"""

DUNGEON_ART = """
######################
#....................#
#..b...####.####..b..#
#......#.......#.....#
#.##...#..$.$..#..##.#
#.##...#...D...#..##.#
#.##...#.......#..##.#
#......##.....##.....#
#..!........?....b...#
#....................#
##########+###########
"""

BOMBADIL_ART = """
############
#.T......G.#
#..........#
#....R.....#
#....s.....#
#####+######
"""

BARROW_ART = """
#############
#...........#
#..#.....#..#
#..#.V.X.#..#
#..#.....#..#
#.....s.....#
######+######
"""

# a little reed-fringed island in the river, caught at first light
DAWN_ART = """
~~~~~~~~~~~~~
~~~,,.&.,,~~~
~~,.......,~~
~,....p....,~
~,.........,~
~~,...s...,~~
~~~,.....,~~~
~~~~~=+=~~~~~
~~~~~~~~~~~~~
"""


def make_overworld():
    W, H = 96, 40
    rng = random.Random()
    grid = [["." for _ in range(W)] for _ in range(H)]

    # scattered grass and trees
    for y in range(H):
        for x in range(W):
            r = rng.random()
            if r < 0.10:
                grid[y][x] = ","
            elif r < 0.20:
                grid[y][x] = "&"

    # dense forest blob around the campfire
    for _ in range(900):
        x = rng.randint(24, 48)
        y = rng.randint(12, 28)
        if rng.random() < 0.45:
            grid[y][x] = "&"

    # northern range + north-east massif
    for y in range(0, 6):
        for x in range(W):
            if rng.random() < 0.92:
                grid[y][x] = "^"
    for y in range(0, 15):
        for x in range(58, W):
            if rng.random() < 0.85:
                grid[y][x] = "^"

    # river, north to south, with a lake at its mouth
    rx = 48
    river_x = {}
    for y in range(H):
        rx = max(42, min(56, rx + rng.choice((-1, 0, 0, 1))))
        river_x[y] = rx
        for dx in (0, 1):
            grid[y][rx + dx] = "~"
    lake_cx, lake_cy = 50, 33
    for y in range(H):
        for x in range(W):
            dx = (x - lake_cx) / 9.0
            dy = (y - lake_cy) / 4.0
            if dx * dx + dy * dy <= 1.0:
                grid[y][x] = "~"

    # the bridge
    by = 19
    bx = river_x[by]
    for dx in (-1, 0, 1, 2):
        grid[by][bx + dx] = "="

    ow = GameMap("overworld", "the Wild", grid)

    def carve(x0, y0, x1, y1):
        """L-shaped trail; water becomes planks, rock becomes path."""
        x, y = x0, y0
        while x != x1:
            x += 1 if x1 > x else -1
            if grid[y][x] == "~":
                grid[y][x] = "="
            elif not TILES[grid[y][x]][1]:
                grid[y][x] = "."
        while y != y1:
            y += 1 if y1 > y else -1
            if grid[y][x] == "~":
                grid[y][x] = "="
            elif not TILES[grid[y][x]][1]:
                grid[y][x] = "."

    # key places
    tower_door = (13, 12)      # wizard's tower, north-west
    hobbit_door = (11, 27)     # hobbit hole, west
    camp = (34, 20)            # campfire clearing, mid-forest
    moomin_door = (66, 30)     # moominhouse, by the lake
    cave_mouth = (68, 9)       # dank cave, in the crags
    gate = (86, 6)             # the Great Gate of the dragon's mountain
    bombadil_door = (78, 33)   # Tom Bombadil's house, in the eastern meadow
    barrow_mound = (86, 34)    # the barrow, out on the silent downs
    descent = (72, 12)         # the deep stair, down among the eastern crags

    # trails first, so buildings stamp over their ends cleanly
    carve(camp[0], camp[1], tower_door[0], tower_door[1] + 2)
    carve(camp[0], camp[1], hobbit_door[0], hobbit_door[1] + 2)
    carve(camp[0], camp[1], bx, by)
    carve(bx + 2, by, moomin_door[0], moomin_door[1] + 2)
    carve(camp[0], camp[1], cave_mouth[0], cave_mouth[1] + 1)
    carve(cave_mouth[0], cave_mouth[1] + 1, gate[0], gate[1] + 1)
    carve(cave_mouth[0], cave_mouth[1] + 1, descent[0], descent[1] + 1)
    carve(moomin_door[0] + 2, moomin_door[1] + 2, bombadil_door[0], bombadil_door[1] + 2)
    carve(bombadil_door[0], bombadil_door[1] + 2, barrow_mound[0], barrow_mound[1] + 1)

    def stamp_building(door_x, door_y):
        """3x3 hut whose south wall holds the door; clears a yard."""
        for y in range(door_y - 2, door_y + 3):
            for x in range(door_x - 2, door_x + 3):
                if 0 <= x < W and 0 <= y < H and not TILES[grid[y][x]][1]:
                    grid[y][x] = "."
        for y in range(door_y - 2, door_y + 1):
            for x in range(door_x - 1, door_x + 2):
                grid[y][x] = "#"
        grid[door_y][door_x] = "+"
        grid[door_y + 1][door_x] = "."

    def stamp_mound(door_x, door_y):
        """a grassy barrow of heaped earth and stone, with a low door south."""
        for y in range(door_y - 2, door_y + 3):
            for x in range(door_x - 2, door_x + 3):
                if 0 <= x < W and 0 <= y < H and not TILES[grid[y][x]][1]:
                    grid[y][x] = "."
        for y in range(door_y - 2, door_y + 1):
            for x in range(door_x - 1, door_x + 2):
                grid[y][x] = "^"
        grid[door_y][door_x] = "+"
        grid[door_y + 1][door_x] = "."

    stamp_building(*tower_door)
    stamp_building(*hobbit_door)
    stamp_building(*moomin_door)
    stamp_building(*bombadil_door)
    stamp_mound(*barrow_mound)
    grid[cave_mouth[1]][cave_mouth[0]] = "o"
    grid[cave_mouth[1] + 1][cave_mouth[0]] = "."
    grid[gate[1]][gate[0]] = "O"
    grid[gate[1] + 1][gate[0]] = "."

    # the deep stair: clear a little landing in the rock, set the downward stair
    for y in range(descent[1] - 1, descent[1] + 2):
        for x in range(descent[0] - 1, descent[0] + 2):
            if 0 <= x < W and 0 <= y < H and not TILES[grid[y][x]][1]:
                grid[y][x] = "."
    grid[descent[1]][descent[0]] = ">"
    grid[descent[1] + 1][descent[0]] = "."

    # a little jetty on the lake's north shore, where a boat waits to be
    # sculled up-river to the Gates of Dawn
    dawn_landing = (50, 28)
    for x in range(dawn_landing[0] - 1, dawn_landing[0] + 2):
        y = dawn_landing[1] - 1
        if not TILES[grid[y][x]][1]:
            grid[y][x] = "."
    grid[dawn_landing[1]][dawn_landing[0]] = "="

    # campfire and Snufkin's clearing
    cx, cy = camp
    for y in range(cy - 2, cy + 3):
        for x in range(cx - 3, cx + 4):
            if grid[y][x] == "&":
                grid[y][x] = "."
    grid[cy][cx] = "*"

    # herbs scattered through the wild
    herb_keys = ["kingsfoil", "kingsfoil", "kingsfoil", "moonpetal",
                 "moonpetal", "bittermoss", "bittermoss", "dreamleaf"]
    placed = 0
    while placed < 26:
        x, y = rng.randint(2, W - 3), rng.randint(7, H - 2)
        if ow.passable(x, y) and (x, y) not in ow.items:
            ow.items[(x, y)] = Item(rng.choice(herb_keys))
            placed += 1
    ow.add_item("stone", 30, 24)
    ow.add_item("pearl", bx - 3, by + 2)
    ow.add_item("kettle", 20, 33)
    ow.add_item("fishingrod", 37, 33)

    # the locals
    ow.add_npc("snufkin", cx + 2, cy)
    ow.add_npc("robinhood", cx - 2, cy)
    ow.add_npc("troll", bx - 2, by + 1)
    ow.add_npc("tomte", hobbit_door[0] + 4, hobbit_door[1] - 1)
    ow.add_npc("holman", hobbit_door[0] - 3, hobbit_door[1] + 2)
    ow.add_npc("fisherman", 38, 32)
    ow.add_npc("tooticky", moomin_door[0] + 4, moomin_door[1] + 1)
    ow.add_npc("hatti", 60, 36)
    ow.add_npc("groke", 24, 36)
    ow.add_npc("wisp", bx + 4, by + 6)
    ow.add_npc("wolf", 40, 14)
    ow.add_npc("wolf", 28, 16)
    for key, count in (("fox", 2), ("raven", 2), ("deer", 3),
                       ("hedgehog", 2), ("squirrel", 3)):
        for _ in range(count):
            for _try in range(60):
                x, y = rng.randint(4, W - 5), rng.randint(8, H - 3)
                if ow.passable(x, y) and not ow.npc_at(x, y):
                    ow.npcs.append(NPC(key, x, y))
                    break

    anchors = {
        "tower": tower_door, "hobbit": hobbit_door, "moomin": moomin_door,
        "cave": cave_mouth, "gate": gate, "camp": (cx + 1, cy),
        "bombadil": bombadil_door, "barrow": barrow_mound, "descent": descent,
        "dawn": dawn_landing,
    }
    return ow, anchors


# ---------------------------------------------------------------- the deep

def _rects_overlap(a, b, pad=0):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return (ax - pad < bx + bw and ax + aw + pad > bx and
            ay - pad < by + bh and ay + ah + pad > by)


def _carve_corridor(grid, c1, c2):
    """An L-shaped tunnel of floor between two room centers."""
    x1, y1 = c1
    x2, y2 = c2
    x = x1
    while x != x2:
        x += 1 if x2 > x else -1
        if grid[y1][x] == "#":
            grid[y1][x] = "."
    y = y1
    while y != y2:
        y += 1 if y2 > y else -1
        if grid[y][x2] == "#":
            grid[y][x2] = "."


def populate_deep(gmap, depth, rooms, rng):
    """Fill a deep level with its proper inhabitants and a little loot.
    rooms[0] is the entry (never stocked); rooms[-1] is the far end."""
    inner = rooms[1:]

    def scatter(key, cx, cy):
        gmap.add_npc(key, cx + rng.randint(-1, 1), cy + rng.randint(-1, 1))

    if depth == 1:
        peaceful = ["gnome", "gnome", "badger", "mole", "shrew"]
        for cx, cy in inner:
            for _ in range(rng.randint(1, 2)):
                scatter(rng.choice(peaceful), cx, cy)
        # the delvers leave small kindnesses lying about
        gmap.add_item("glowcap", inner[0][0], inner[0][1])
        gmap.add_item("bittermoss", rooms[-1][0], rooms[-1][1])
        gmap.add_item("kingsfoil", inner[len(inner) // 2][0],
                      inner[len(inner) // 2][1])
    elif depth == 2:
        for cx, cy in inner:
            for _ in range(rng.randint(1, 2)):
                scatter("orc" if rng.random() < 0.4 else "goblin", cx, cy)
        # one gnome who took a very wrong turn, and a warm cloak off a corpse
        scatter("gnome", inner[0][0], inner[0][1])
        gmap.add_item("eldercloak", rooms[-1][0], rooms[-1][1])
        gmap.add_item("potion_heal", inner[len(inner) // 2][0],
                      inner[len(inner) // 2][1])
    else:  # depth == 3, the pit
        for cx, cy in inner[:-1]:
            scatter("orc" if rng.random() < 0.5 else "goblin", cx, cy)
        # the Baalrukh waits at the very bottom
        gmap.add_npc("balgorg", rooms[-1][0], rooms[-1][1])


def make_deep_level(name, title, depth, rng, w=44, h=22):
    """A procedurally generated level of rooms and tunnels, all in the dark.
    Returns (map, up_pos, down_pos); down_pos is None at the very bottom."""
    grid = [["#" for _ in range(w)] for _ in range(h)]
    rects, rooms = [], []
    attempts = 0
    while len(rects) < 8 and attempts < 300:
        attempts += 1
        rw, rh = rng.randint(4, 8), rng.randint(3, 5)
        rx, ry = rng.randint(1, w - rw - 2), rng.randint(1, h - rh - 2)
        new = (rx, ry, rw, rh)
        if any(_rects_overlap(new, o, pad=1) for o in rects):
            continue
        for y in range(ry, ry + rh):
            for x in range(rx, rx + rw):
                grid[y][x] = "."
        rects.append(new)
        rooms.append((rx + rw // 2, ry + rh // 2))
    # thread every room onto one path, so the far end is always reachable
    for i in range(1, len(rooms)):
        _carve_corridor(grid, rooms[i - 1], rooms[i])

    up, down = rooms[0], rooms[-1]
    grid[up[1]][up[0]] = "<"
    if depth < 3:
        grid[down[1]][down[0]] = ">"

    gmap = GameMap(name, title, grid, dark=True)
    populate_deep(gmap, depth, rooms, rng)
    return gmap, up, (down if depth < 3 else None)


def build_world():
    maps = {}
    ow, anchors = make_overworld()
    maps["overworld"] = ow

    tower, tower_start, tower_door = parse_interior(
        "tower", "the Wizard's Tower",
        TOWER_ART,
        {"Z": ("npc", "wizard"), "B": ("npc", "bookshelf"), "C": ("npc", "cauldron"),
         "w": ("item", "hazelwand"), "?": ("item", "scroll_hush"), "s": ("start",)})
    moomin, moomin_start, moomin_door = parse_interior(
        "moominhouse", "the Moominhouse",
        MOOMIN_ART,
        {"M": ("npc", "mamma"), "P": ("npc", "pappa"), "y": ("npc", "littlemy"),
         "C": ("npc", "stove"), "j": ("item", "jam"), "s": ("start",)})
    hobbit, hobbit_start, hobbit_door = parse_interior(
        "hobbithole", "the Hobbit-hole",
        HOBBIT_ART,
        {"a": ("npc", "dora"), "k": ("item", "seedcake"), "{": ("item", "lantern"),
         "%": ("item", "seedcake"), "s": ("start",)})
    cave, cave_start, cave_door = parse_interior(
        "cave", "the Dark Dank Cave",
        CAVE_ART,
        {"w": ("npc", "witch"), "m": ("item", "glowcap"),
         "e": ("item", "scroll_ember"), "r": ("item", "scroll_glimmer"),
         "s": ("start",)},
        dark=True)
    dungeon, _, dungeon_door = parse_interior(
        "dungeon", "the Mountain Dungeon",
        DUNGEON_ART,
        {"D": ("npc", "dragon"), "b": ("npc", "bats"), "$": ("item", "coin"),
         "!": ("item", "helm"), "?": ("item", "scroll_hush")},
        dark=True)
    bombadil, bombadil_start, bombadil_idoor = parse_interior(
        "bombadil", "Tom Bombadil's House",
        BOMBADIL_ART,
        {"T": ("npc", "tombombadil"), "G": ("npc", "goldberry"),
         "R": ("npc", "roverandom"), "s": ("start",)})
    barrow, _, barrow_idoor = parse_interior(
        "barrow", "the Barrow",
        BARROW_ART,
        {"V": ("npc", "barrowwight"), "X": ("item", "dragonsword"),
         "s": ("start",)},
        dark=True)
    dawn, dawn_start, dawn_idoor = parse_interior(
        "gatesofdawn", "the Gates of Dawn",
        DAWN_ART,
        {"p": ("npc", "piper"), "s": ("start",)})
    deep_rng = random.Random()
    deep1, d1_up, d1_down = make_deep_level("deep1", "the Deep Delvings", 1, deep_rng)
    deep2, d2_up, d2_down = make_deep_level("deep2", "the Goblin Warrens", 2, deep_rng)
    deep3, d3_up, _ = make_deep_level("deep3", "the Pit of Balgorg", 3, deep_rng)

    cave.add_item("glowcap", 9, 1)
    dungeon.add_item("coin", 3, 9)
    dungeon.add_item("eldercloak", 18, 1)
    # the witch leaves her recipes lying about; others copied them long ago
    cave.add_item("recipe_heal", 11, 4)
    tower.add_item("recipe_moon", 8, 5)
    moomin.add_item("recipe_dream", 7, 1)

    for m in (tower, moomin, hobbit, cave, dungeon, bombadil, barrow, dawn,
              deep1, deep2, deep3):
        maps[m.name] = m

    def link(outside_pos, inside_map, inside_pos):
        ow.links[outside_pos] = (inside_map.name, inside_pos)
        inside_map.links[inside_pos] = ("overworld", outside_pos)

    link(anchors["tower"], tower, tower_door)
    link(anchors["hobbit"], hobbit, hobbit_door)
    link(anchors["moomin"], moomin, moomin_door)
    link(anchors["cave"], cave, cave_door)
    link(anchors["gate"], dungeon, dungeon_door)
    link(anchors["bombadil"], bombadil, bombadil_idoor)
    link(anchors["barrow"], barrow, barrow_idoor)
    link(anchors["dawn"], dawn, dawn_idoor)

    # the deep is a chain of stairs: you arrive beside a stair and walk onto
    # the matching one to go the other way. entries sit next to the stairs
    # (find_open steps off the stair tile itself).
    d1_up_at = deep1.find_open(*d1_up)
    d1_down_at = deep1.find_open(*d1_down)
    d2_up_at = deep2.find_open(*d2_up)
    d2_down_at = deep2.find_open(*d2_down)
    d3_up_at = deep3.find_open(*d3_up)

    ow.links[anchors["descent"]] = ("deep1", d1_up_at)
    deep1.links[d1_up] = ("overworld", anchors["descent"])
    deep1.links[d1_down] = ("deep2", d2_up_at)
    deep2.links[d2_up] = ("deep1", d1_down_at)
    deep2.links[d2_down] = ("deep3", d3_up_at)
    deep3.links[d3_up] = ("deep2", d2_down_at)

    starts = {
        "ranger": ("overworld", ow.find_open(*anchors["camp"])),
        "wizard's apprentice": ("tower", tower_start),
        "hobbit": ("hobbithole", hobbit_start),
        "moomintroll": ("moominhouse", moomin_start),
        "young witch": ("cave", cave_start),
        "water rat": ("gatesofdawn", dawn_start),
    }
    return maps, starts


# ---------------------------------------------------------------- classes

CLASSES = {
    "1": {
        "name": "ranger",
        "blurb": "knows the trails; starts by the campfire in the forest",
        "hp": 14, "mp": 2, "strength": 4, "sight": 3,
        "spells": [], "items": ["hornknife", "greenhood", "bilberries"],
    },
    "2": {
        "name": "moomintroll",
        "blurb": "soft of heart and paw; starts at the Moominhouse",
        "hp": 12, "mp": 4, "strength": 4, "sight": 2,
        "spells": [], "items": ["ladle", "scarf", "pancake"],
    },
    "3": {
        "name": "hobbit",
        "blurb": "fond of pantries; starts at home in the hobbit-hole",
        "hp": 10, "mp": 2, "strength": 2, "sight": 2,
        "spells": [], "items": ["walkingstick", "waistcoat", "seedcake"],
    },
    "4": {
        "name": "wizard's apprentice",
        "blurb": "knows three charms and a half; starts at the tower",
        "hp": 8, "mp": 8, "strength": 2, "sight": 2,
        "spells": ["glimmer", "emberkindle", "hushword"],
        "items": ["oakstaff", "patchrobe"],
    },
    "5": {
        "name": "young witch",
        "blurb": "knows every brew by heart; starts in the dank cave",
        "hp": 10, "mp": 5, "strength": 2, "sight": 3,
        "spells": [], "items": ["broom", "pointyhat"],
        "recipes": ["healing draught", "moonlight cordial", "dream tea"],
    },
    "6": {
        "name": "water rat",
        "blurb": "messes about in boats; wakes at the Gates of Dawn",
        "hp": 12, "mp": 3, "strength": 3, "sight": 3,
        "spells": [], "items": ["oar", "boatcoat", "picnic", "fishingrod"],
    },
}

AMBIENT_WILD = [
    "A chaffinch sings somewhere above.",
    "The wind combs through the grass.",
    "Far off, a cuckoo counts somebody's years.",
    "It smells like rain that hasn't made up its mind.",
    "A woodpecker knocks, politely, twice.",
    "Somewhere a brook is laughing at its own joke.",
    "The clouds rearrange themselves without consulting anyone.",
]

AMBIENT_DARK = [
    "Water drips, counting out the dark.",
    "The air tastes of cold stone and old smoke.",
    "Something small skitters away, embarrassed.",
    "The dark leans in a little, then thinks better of it.",
]


# ---------------------------------------------------------------- game


class Game:
    def __init__(self, cls, get_key=read_key, out=None):
        self.get_key = get_key
        self.out = out if out is not None else sys.stdout
        self.maps, starts = build_world()
        self.cls = cls
        self.map_name, (self.x, self.y) = starts[cls["name"]]
        self.start = (self.map_name, (self.x, self.y))
        self.hp = self.maxhp = cls["hp"]
        self.mp = self.maxmp = cls["mp"]
        self.strength = cls["strength"]
        self.sight = cls["sight"]
        self.spells = list(cls["spells"])
        self.recipes = list(cls.get("recipes", []))
        self.inv = [Item(k) for k in cls["items"]]
        self.weapon = next((i for i in self.inv if i.kind == "weapon"), None)
        self.cloak = next((i for i in self.inv if i.kind == "cloak"), None)
        self.light_turns = 0
        self.fish_stock = random.sample(FISH_KEYS, random.randint(3, 4))
        self.turn = 0
        self.running = True
        self.msgs = []
        self.say("You set out into a soft green morning. (? for help)")

    # -- helpers ---------------------------------------------------------

    @property
    def cur(self):
        return self.maps[self.map_name]

    def say(self, text):
        self.msgs.append(text)
        self.msgs = self.msgs[-60:]

    def light_radius(self):
        if not self.cur.dark:
            return 99
        r = self.sight
        if any(i.kind == "light" for i in self.inv):
            r = max(r, 4)
        if self.light_turns > 0:
            r = max(r, 6)
        return r

    # -- main step ---------------------------------------------------------

    def step(self, key):
        acted = False
        if key in DIRS:
            acted = self.try_move(*DIRS[key])
        elif key == "g":
            acted = self.pick_up()
        elif key == "i":
            self.inventory_menu()
        elif key == "z":
            acted = self.cast_menu()
        elif key == "m":
            acted = self.mix_menu()
        elif key == "f":
            acted = self.fight()
        elif key in (" ", "."):
            acted = True
            self.say("You wait, and the world goes about its business.")
        elif key == "?":
            self.help_screen()
        elif key in ("q", "Q"):
            self.say("Leave the Wild for now? (y/n)")
            self.refresh()
            if self.get_key() == "y":
                self.running = False
                return
            self.say("The Wild approves of your choice.")
        if acted:
            self.world_turn()

    def try_move(self, dx, dy):
        nx, ny = self.x + dx, self.y + dy
        npc = self.cur.npc_at(nx, ny)
        if npc:
            self.talk(npc)
            return True
        if not self.cur.passable(nx, ny):
            tile = self.cur.tile(nx, ny)
            self.say("There is %s in the way." % TILES[tile][0])
            return False
        self.x, self.y = nx, ny
        if (nx, ny) in self.cur.links:
            dest_map, dest_pos = self.cur.links[(nx, ny)]
            self.map_name = dest_map
            self.x, self.y = dest_pos
            self.say("You enter %s." % self.cur.title
                     if dest_map != "overworld"
                     else "You step out into %s." % self.cur.title)
            return True
        item = self.cur.items.get((nx, ny))
        if item:
            self.say("You see a %s here. (g to gather)" % item.name)
        return True

    def talk(self, npc):
        if npc.hostile:
            if npc.key == "balgorg":
                self.say(npc.say())
            else:
                self.say("%s is in no mood for talk!" % npc.name.capitalize())
            return
        self.say(npc.say())

    def pick_up(self):
        item = self.cur.items.pop((self.x, self.y), None)
        if not item:
            self.say("There is nothing here but the ground, which is doing fine.")
            return False
        self.inv.append(item)
        self.say("You take the %s." % item.name)
        if item.key == "silmaril":
            self.say("The deep is very quiet now. You hold a Silmaril, and its "
                     "light does not waver, not even here at the bottom of the "
                     "world. There is nothing left to fetch, and no one left to "
                     "ask. The long stair, when you climb it, will smell of "
                     "morning. Go home. You have done a great thing.")
        if self.map_name == "dungeon":
            dragon = next((n for n in self.cur.npcs if n.key == "dragon"), None)
            if dragon and not dragon.hostile:
                dragon.hostile = True
                self.say("THE DRAGON'S EYE SNAPS OPEN. 'THIEF!' IT ROARS. "
                         "'I SAID TOUCH NOTHING!' THE OLD DRAGON IS COMING FOR YOU!")
        return True

    # -- fighting (discouraged, but possible) --------------------------------

    def fight(self):
        self.say("Strike which way? (movement key)")
        self.refresh()
        key = self.get_key()
        if key not in DIRS:
            self.say("You lower your hand. Wise.")
            return False
        dx, dy = DIRS[key]
        npc = self.cur.npc_at(self.x + dx, self.y + dy)
        if not npc:
            self.say("You swat the empty air. The air forgives you.")
            return True
        if npc.key in SCENERY:
            self.say("You thump %s. It takes this stoically." % npc.name)
            return True
        if npc.key == "dragon" and self.weapon and self.weapon.key == "dragonsword":
            self.say("The ancient blade flares with cold fire and knows its one "
                     "purpose. You strike but once, and the old dragon's long "
                     "doom is sealed.")
            self.kill_npc(npc)
            return True
        dmg = max(1, self.strength + (self.weapon.power if self.weapon else 0)
                  + random.randint(-1, 1))
        npc.hp -= dmg
        npc.hostile = True
        if npc.hp <= 0:
            self.kill_npc(npc)
        else:
            self.say("You strike %s. It does not thank you." % npc.name)
        return True

    def kill_npc(self, npc):
        self.cur.npcs.remove(npc)
        if npc.key == "dragon":
            self.say("The old dragon shudders, sighs out a century of smoke, "
                     "and is still. Something warm gleams in the ashes.")
            self.cur.items[(npc.x, npc.y)] = Item("dragonheart")
        elif npc.key == "balgorg":
            self.say("Balgorg the Baalrukh lets out a cry that shakes dust from "
                     "the roots of the mountain. The shadow and the flame come "
                     "apart, and are gone. Where it stood, a single jewel burns "
                     "with a pure and ancient light.")
            self.cur.items[(npc.x, npc.y)] = Item("silmaril")
        else:
            self.say("%s slips away into the otherworld. The Wild is quieter, "
                     "and not better." % npc.name.capitalize())

    # -- magic ----------------------------------------------------------------

    def cast_menu(self):
        if not self.spells:
            self.say("You know no charms. The wizard's tower has books; "
                     "scrolls turn up in dark places.")
            return False
        lines = ["You know these charms:"]
        for i, sp in enumerate(self.spells):
            cost, blurb = SPELLS[sp]
            lines.append("  %d) %s (%d mp) — %s" % (i + 1, sp, cost, blurb))
        lines.append("Which? (number, anything else to stop)")
        self.say(" ".join(lines))
        self.refresh()
        key = self.get_key()
        if not key.isdigit() or not (1 <= int(key) <= len(self.spells)):
            self.say("The words stay unspoken.")
            return False
        spell = self.spells[int(key) - 1]
        cost = SPELLS[spell][0]
        if self.mp < cost:
            self.say("You reach for the charm and find the well dry. "
                     "Moonpetal would help.")
            return False
        if spell == "glimmer":
            self.mp -= cost
            self.light_turns = 60
            self.say("A small kind light gathers at your shoulder and stays.")
            return True
        # directional charms
        self.say("Toward where? (movement key)")
        self.refresh()
        dkey = self.get_key()
        if dkey not in DIRS:
            self.say("The charm fizzles politely.")
            return False
        dx, dy = DIRS[dkey]
        npc = self.cur.npc_at(self.x + dx, self.y + dy)
        self.mp -= cost
        if spell == "emberkindle":
            if npc:
                dmg = 4 + random.randint(0, 2)
                npc.hp -= dmg
                npc.hostile = True
                if npc.hp <= 0:
                    self.kill_npc(npc)
                else:
                    self.say("A spark leaps and singes %s. It is not amused."
                             % npc.name)
            else:
                self.say("The spark gutters out on the damp ground.")
        elif spell == "hushword":
            if npc and npc.hostile:
                npc.hostile = False
                self.say("You speak the hushword. %s settles, like a kettle "
                         "taken off the heat." % npc.name.capitalize())
            elif npc:
                self.say("%s was already calm, but appreciates the thought."
                         % npc.name.capitalize())
            else:
                self.say("The hush settles on nothing in particular. Restful.")
        return True

    # -- mixing -----------------------------------------------------------

    def have_herbs(self, ingredients):
        pool = [i.key for i in self.inv]
        for k in ingredients:
            if k not in pool:
                return False
            pool.remove(k)
        return True

    def mix_menu(self):
        if not self.recipes:
            self.say("You know no recipes. The bog-witch writes hers down, "
                     "and so do others, here and there.")
            return False
        lines = ["You know these brews:"]
        for i, name in enumerate(self.recipes):
            ingredients, _, blurb = RECIPES[name]
            herbs = " + ".join(ITEM_DEFS[k][0] for k in ingredients)
            mark = "" if self.have_herbs(ingredients) else " [herbs missing]"
            lines.append("%d) %s (%s) — %s%s"
                         % (i + 1, name, herbs, blurb, mark))
        lines.append("Mix which? (number, anything else to stop)")
        self.say(" ".join(lines))
        self.refresh()
        key = self.get_key()
        if not key.isdigit() or not (1 <= int(key) <= len(self.recipes)):
            self.say("The herbs stay in your pack, unbothered.")
            return False
        name = self.recipes[int(key) - 1]
        ingredients, product, _ = RECIPES[name]
        if not self.have_herbs(ingredients):
            missing = [ITEM_DEFS[k][0] for k in ingredients
                       if not any(i.key == k for i in self.inv)]
            self.say("You lack the makings: %s. The Wild grows what it grows; "
                     "go and look." % ", ".join(missing))
            return False
        for k in ingredients:
            self.inv.remove(next(i for i in self.inv if i.key == k))
        brew = Item(product)
        self.inv.append(brew)
        self.say("You crush, steep, and mutter over the herbs, the way the "
                 "recipe says. You now carry a %s." % brew.name)
        return True

    # -- inventory ----------------------------------------------------------

    def inventory_menu(self):
        if not self.inv:
            self.say("Your pockets hold nothing but a little forest air.")
            return
        rows = [CLEAR, "  — your pack —", ""]
        for i, item in enumerate(self.inv):
            tag = ""
            if item is self.weapon:
                tag = " (in hand)"
            if item is self.cloak:
                tag = " (worn)"
            rows.append("  %s) %s%s" % (chr(ord("a") + i), item.name, tag))
            rows.append("       %s" % item.desc)
        rows.append("")
        rows.append("  Choose a letter to use/eat/wear, anything else to close.")
        self.out.write("\n".join(rows) + "\n")
        self.out.flush()
        key = self.get_key()
        idx = ord(key) - ord("a") if len(key) == 1 else -1
        if 0 <= idx < len(self.inv):
            self.use_item(self.inv[idx])

    def use_item(self, item):
        if item.kind in ("herb", "food"):
            self.inv.remove(item)
            if item.key == "moonpetal":
                self.mp = min(self.maxmp, self.mp + 4)
                self.say("The moonpetal melts on your tongue like cool light.")
            elif item.key == "glowcap":
                self.mp = min(self.maxmp, self.mp + 3)
                self.light_turns = max(self.light_turns, 20)
                self.say("The glowcap tastes of deep places. "
                         "Your eyes drink the dark more easily.")
            elif item.key == "dreamleaf":
                self.hp = min(self.maxhp, self.hp + 1)
                self.say("You chew the dreamleaf. For a while, "
                         "the clouds look back, kindly.")
            else:
                self.hp = min(self.maxhp, self.hp + item.power)
                self.say("You eat the %s. (+%d) That's better."
                         % (item.name, item.power))
        elif item.kind == "weapon":
            self.weapon = item
            self.say("You take up the %s." % item.name)
        elif item.kind == "cloak":
            self.cloak = item
            self.say("You put on the %s." % item.name)
        elif item.kind == "scroll":
            spell = SCROLL_SPELL[item.key]
            if spell in self.spells:
                self.say("You already know %s. The scroll seems pleased anyway."
                         % spell)
            else:
                self.spells.append(spell)
                self.inv.remove(item)
                self.say("You sound out the careful letters... and the charm "
                         "of %s is yours. The scroll sighs into dust." % spell)
        elif item.kind == "recipe":
            recipe = RECIPE_SCROLL[item.key]
            if recipe in self.recipes:
                self.say("You already know how to brew %s. Still, it never "
                         "hurts to check one's measures." % recipe)
            else:
                self.recipes.append(recipe)
                self.inv.remove(item)
                self.say("You read the recipe twice, the way you should... "
                         "and the brewing of %s is yours. (m to mix)" % recipe)
        elif item.kind == "potion":
            self.inv.remove(item)
            if item.key == "potion_heal":
                self.hp = min(self.maxhp, self.hp + item.power)
                self.say("You drink the healing draught. Warmth goes through "
                         "you like good news. (+%d)" % item.power)
            elif item.key == "potion_moon":
                self.mp = self.maxmp
                self.light_turns = max(self.light_turns, 40)
                self.say("You drink the moonlight cordial. The well of magic "
                         "brims, and the dark steps back to a polite distance.")
            elif item.key == "potion_dream":
                calmed = 0
                for npc in self.cur.npcs:
                    dist = max(abs(npc.x - self.x), abs(npc.y - self.y))
                    if npc.hostile and dist <= 5:
                        npc.hostile = False
                        calmed += 1
                self.hp = min(self.maxhp, self.hp + 1)
                if calmed:
                    self.say("The steam of the dream tea drifts out, smelling "
                             "of slow afternoons. Tempers nearby settle like "
                             "leaves on a pond.")
                else:
                    self.say("You sip the dream tea. Nothing nearby needed "
                             "calming, so it calms you instead.")
        elif item.kind == "light":
            self.say("The lantern is lit and doing its best. "
                     "Carrying it keeps the dark polite.")
        elif item.kind == "rod":
            self.go_fishing()
        else:
            self.say("%s — %s" % (item.name, item.desc))

    # -- fishing --------------------------------------------------------------

    def go_fishing(self):
        near_water = any(self.cur.tile(self.x + dx, self.y + dy) == "~"
                         for dx in (-1, 0, 1) for dy in (-1, 0, 1))
        if not near_water:
            self.say("You give the line a hopeful flick, but the nearest "
                     "water is elsewhere, minding its own business.")
            return
        if not self.fish_stock:
            self.say("You cast, and wait, and nothing so much as ripples. "
                     "The quiet has a settled, final sort of feel to it.")
            return
        if random.random() < FISH_CHANCE:
            fish = Item(self.fish_stock.pop(random.randrange(len(self.fish_stock))))
            self.inv.append(fish)
            self.say("The line goes taut! You land a %s." % fish.name)
            if not self.fish_stock:
                self.say("As you coil the line, a curious feeling settles over "
                         "you, quiet as dusk: your fishing luck has run out. "
                         "The water has given all it means to give.")
        else:
            self.say(random.choice(FISHING_MISSES))
        self.world_turn()

    # -- the world's turn ------------------------------------------------------

    def world_turn(self):
        self.turn += 1
        if self.light_turns > 0:
            self.light_turns -= 1
            if self.light_turns == 0:
                self.say("Your little light bows and goes out.")
        # rest by the fire
        near_fire = any(self.cur.tile(self.x + dx, self.y + dy) == "*"
                        for dx in (-1, 0, 1) for dy in (-1, 0, 1))
        if near_fire and self.turn % 3 == 0:
            if self.hp < self.maxhp or self.mp < self.maxmp:
                self.hp = min(self.maxhp, self.hp + 1)
                self.mp = min(self.maxmp, self.mp + 1)
                self.say("The fire warms you through.")
        elif self.turn % 10 == 0:
            self.hp = min(self.maxhp, self.hp + 1)
            self.mp = min(self.maxmp, self.mp + 1)
        # creatures
        for npc in list(self.cur.npcs):
            if npc.key in SCENERY:
                continue
            dist = max(abs(npc.x - self.x), abs(npc.y - self.y))
            if npc.hostile and dist == 1:
                if npc.key == "balgorg":
                    if any(i.key == "dragonheart" for i in self.inv):
                        dmg = random.randint(1, 3)
                        self.hp -= dmg
                        self.say("Balgorg's blade of fire comes down — but the "
                                 "dragon's heart blazes at your breast and turns "
                                 "the worst of it aside. (-%d)" % dmg)
                    else:
                        self.say("Balgorg's flaming sword comes down, and there "
                                 "is no cold thing in all the world to answer it. "
                                 "The fire takes you whole.")
                        self.hp = 0
                    if self.hp <= 0:
                        self.swoon()
                        return
                    continue
                defense = self.cloak.power if self.cloak else 0
                dmg = max(1, npc.strength - defense + random.randint(-1, 1))
                self.hp -= dmg
                self.say("%s strikes at you! (-%d)" % (npc.name.capitalize(), dmg))
                if self.hp <= 0:
                    self.swoon()
                    return
            elif npc.hostile and dist <= 6:
                self.npc_step_toward(npc)
            elif not npc.static and random.random() < 0.3:
                self.npc_wander(npc)
        # ambience
        if random.random() < 0.05:
            pool = AMBIENT_DARK if self.cur.dark else AMBIENT_WILD
            self.say(random.choice(pool))

    def npc_wander(self, npc):
        dx, dy = random.choice(list(DIRS.values()))
        self.npc_try_step(npc, dx, dy)

    def npc_step_toward(self, npc):
        dx = (self.x > npc.x) - (self.x < npc.x)
        dy = (self.y > npc.y) - (self.y < npc.y)
        if dx and dy:
            dx, dy = random.choice(((dx, 0), (0, dy)))
        self.npc_try_step(npc, dx, dy)

    def npc_try_step(self, npc, dx, dy):
        nx, ny = npc.x + dx, npc.y + dy
        if (self.cur.passable(nx, ny) and not self.cur.npc_at(nx, ny)
                and (nx, ny) != (self.x, self.y)
                and (nx, ny) not in self.cur.links):
            npc.x, npc.y = nx, ny

    def swoon(self):
        self.say("Everything goes soft and grey...")
        self.map_name, (self.x, self.y) = self.start
        self.x, self.y = self.cur.find_open(self.x, self.y)
        self.hp = self.maxhp
        self.mp = self.maxmp
        for m in self.maps.values():
            for npc in m.npcs:
                npc.hostile = npc.key in HOSTILE
        self.say("...and you wake where you began, aching but whole. "
                 "The Wild has carried you home. It does that.")

    # -- drawing ----------------------------------------------------------------

    def render(self):
        term = shutil.get_terminal_size((100, 32))
        vw = max(40, min(term.columns - 2, self.cur.w))
        vh = max(12, min(term.lines - 8, self.cur.h))
        cam_x = max(0, min(self.cur.w - vw, self.x - vw // 2))
        cam_y = max(0, min(self.cur.h - vh, self.y - vh // 2))
        radius = self.light_radius()
        npc_pos = {(n.x, n.y): n for n in self.cur.npcs}

        out = [CLEAR]
        out.append(col("1;33", " ROGUES WILD ") + col("90", "· ")
                   + col("97", self.cur.title) + "\n")
        for sy in range(vh):
            row = [" "]
            for sx in range(vw):
                x, y = cam_x + sx, cam_y + sy
                visible = max(abs(x - self.x), abs(y - self.y)) <= radius
                if visible:
                    self.cur.seen.add((x, y))
                if (x, y) == (self.x, self.y):
                    row.append(col("1;97", "@"))
                elif visible and (x, y) in npc_pos:
                    n = npc_pos[(x, y)]
                    c = "1;91" if n.hostile else n.color
                    row.append(col(c, n.glyph))
                elif visible and (x, y) in self.cur.items:
                    it = self.cur.items[(x, y)]
                    row.append(col(it.color, it.glyph))
                elif visible:
                    tile = self.cur.tile(x, y)
                    row.append(col(TILES[tile][2], tile))
                elif (x, y) in self.cur.seen:
                    row.append(col("90", self.cur.tile(x, y)))
                else:
                    row.append(" ")
            out.append("".join(row) + "\n")

        gear = []
        if self.weapon:
            gear.append(self.weapon.name)
        if self.cloak:
            gear.append(self.cloak.name)
        status = (" %s · hp %d/%d · mp %d/%d · %s · turn %d"
                  % (self.cls["name"], self.hp, self.maxhp, self.mp, self.maxmp,
                     ", ".join(gear) if gear else "empty-handed", self.turn))
        out.append(col("1;32", status) + "\n")
        start = max(0, len(self.msgs) - 3)
        for i, m in enumerate(self.msgs[start:], start):
            # cycle white / very light grey so message bounds are clear
            code = "38;5;231" if i % 2 == 0 else "38;5;252"
            for piece in wrap(m, vw - 2):
                out.append(col(code, " " + piece) + "\n")
        return "".join(out)

    def refresh(self):
        self.out.write(self.render())
        self.out.flush()

    def help_screen(self):
        text = (CLEAR + """
  — ROGUES WILD —

  move        arrows or h j k l
  talk        walk into any creature (most have something to say)
  g           gather what lies at your feet
  i           open your pack (eat herbs, wear cloaks, read scrolls)
  z           speak a charm, if you know any
  m           mix a brew, if you know the recipe and carry the herbs
  f           strike something (the Wild would rather you didn't)
  . or space  wait a turn
  q           leave the Wild
  ?           this page

  Doors (+), cave mouths (o) and the Great Gate (O) are walked into.
  Stairs down (>) and up (<) lead into — and out of — the deep places
  under the eastern crags. Go carefully, and armed, and not too soon.
  Caves and the deep are dark: a lantern, a glowcap or GLIMMER helps.
  Herbs (") mend you; the campfire (*) mends you faster; time mends all.
  Recipes (?) teach brews; gathered herbs go into them, and are used up.
  A fishing rod (/), used from your pack beside water, may earn supper.
  Nothing here needs winning. Go and see what's over the hill.

  (press any key)
""")
        self.out.write(text)
        self.out.flush()
        self.get_key()


def wrap(text, width):
    words = text.split()
    lines, line = [], ""
    for w in words:
        if line and len(line) + 1 + len(w) > width:
            lines.append(line)
            line = w
        else:
            line = (line + " " + w).strip()
    if line:
        lines.append(line)
    return lines or [""]


# ---------------------------------------------------------------- intro


def intro():
    sys.stdout.write(CLEAR + """
        ~  R O G U E S   W I L D  ~
       a gentle roguelike of the green world

  The Wild is wide: a wizard's tower in the north hills, a hobbit-hole
  in the west meadow, the Moominhouse down by the lake, a dank cave in
  the crags, old Tom Bombadil's house in the eastern meadows with the
  silent barrow-downs beyond, a reed-fringed island up-river where the
  dawn comes in — and under the mountain, behind the Great Gate,
  something old and golden that everyone keeps asking you to rob.

  And somewhere in the eastern crags, an old stair goes down, and down,
  into the deep places of the world, where the last dark thing waits.

  There is no winning — only weather, and tea, and talk. But there is,
  if you want it, one very old and very heavy thing worth carrying home.

  Who are you?

""")
    for key in sorted(CLASSES):
        c = CLASSES[key]
        sys.stdout.write("    %s) %-22s %s\n" % (key, c["name"], c["blurb"]))
    sys.stdout.write("\n  Choose (1-6): ")
    sys.stdout.flush()
    while True:
        k = read_key()
        if k in CLASSES:
            return CLASSES[k]
        if k in ("q", "Q"):
            sys.exit(0)


def main():
    cls = intro()
    game = Game(cls)
    sys.stdout.write(HIDE_CURSOR)
    try:
        while game.running:
            game.refresh()
            game.step(read_key())
    finally:
        sys.stdout.write(SHOW_CURSOR + RESET + "\n")
    print("The trail will keep. Farewell.\n")


if __name__ == "__main__":
    main()
