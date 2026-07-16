# Rogues Wild

A gentle folklore roguelike for the terminal. Pure Python standard
library — nothing to install.

```
python3 rogues_wild.py
```

There is no winning. There is only weather, and tea, and talk.

## Who you can be

| class               | starts at                  | flavor                          |
|---------------------|----------------------------|---------------------------------|
| ranger              | the campfire in the forest | hardy, sees well in the dark    |
| moomintroll         | the Moominhouse            | soft of heart and paw           |
| hobbit              | the hobbit-hole            | small, brave, well-provisioned  |
| wizard's apprentice | the wizard's tower         | knows three charms and a half   |
| young witch         | the dark dank cave         | knows every brew by heart       |
| water rat           | the Gates of Dawn          | messes about in boats           |

## Keys

| key          | does                                                  |
|--------------|-------------------------------------------------------|
| arrows / hjkl| move (walk into a creature to talk to it)             |
| `g`          | gather what lies at your feet                         |
| `i`          | your pack — eat herbs, wear cloaks, read scrolls      |
| `z`          | speak a charm                                         |
| `f`          | strike something (the Wild would rather you didn't)   |
| `.` / space  | wait                                                  |
| `?`          | help                                                  |
| `q`          | leave                                                 |

## The lay of the land

The overworld is generated fresh each time, but you will always find:
a wizard's tower in the north-west, a hobbit-hole in the west meadow,
the Moominhouse by the southern lake, a campfire clearing in the deep
forest, a dark dank cave in the crags (`o`), and the Great Gate (`O`)
of the mountain dungeon, where something old and golden sleeps.

Up-river, a jetty on the lake's north shore (`=`) carries you out to
the **Gates of Dawn** — a little reed-fringed island where the Piper
keeps the morning, and where the water rat first wakes.

Caves are dark. A lantern, a glowcap mushroom, or the GLIMMER charm
keeps the dark polite. Herbs (`"`) mend you; the campfire mends you
faster; time mends everything else.

Most creatures will talk if you walk into them. Several will tell you
to go steal the dragon's heart. There is no quest system. They just
say that.

## The deep, and the one heavy thing

In the eastern crags a stair (`>`) goes down into a procedurally
generated dungeon, fresh each game. Stairs (`>` down, `<` up) are
walked into, like doors.

* **The Deep Delvings** — quiet burrowing folk: gnomes, a talking
  badger, a forgetful mole, a jittery shrew. They will not harm you,
  and some of them have useful advice.
* **The Goblin Warrens** — goblins and orcs, and they mean it. Come
  armed, or come calm (HUSHWORD and dream tea both still work).
* **The Pit of Balgorg** — at the very bottom waits **Balgorg the
  Baalrukh**, and his sword is living fire. Unprotected, that fire is
  simply fatal. But the **dragon's heart** — won from the old dragon
  under the Great Gate — is colder than any flame, and worn in your
  pack it turns the worst aside. Slay him, and he leaves behind a
  **Silmaril**.

There is still no winning. But the Silmaril is one very old and very
heavy thing worth carrying home.
