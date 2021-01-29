# Base entity class
class Entity(object):
    default_stats = {
        "max_hp": 15,
        "attack": 3,
        "speed": 3,
        "block": 3,
        "passive_defense": 0,
        "magic_attack": 5,
        "magic_defense": 0,
        "mana": 0,
    }

    _stat_list = [
        "HP",
        "Max HP",
        "Attack",
        "Speed",
        "Block",
        "Passive Defense",
        "Magic Attack",
        "Magic Defense",
        "Mana",
    ]

    stat_list = [
        "HP/Max HP",
        "Attack",
        "Speed",
        "Block",
        "Passive Defense",
        "Magic Attack",
        "Magic Defense",
        "Mana",
    ]

    def __init__(self, name="", spellbook={}, *, from_file=False, **kwargs):
        for k, v in Entity.default_stats.items():
            self.default_stats.setdefault(k, v)

        self.stats = self.default_stats.copy()
        self.stats.update(kwargs)
        self.name = name
        self.player = False
        self.player_class = ""
        self.spellbook = spellbook
        self.inventory = []

        if "hp" not in self.stats:
            self.stats["hp"] = self.stats["max_hp"]

        if "current_mana" not in self.stats:
            self.stats["current_mana"] = self.stats["mana"]

        self.blocking = False
        self.enraged = 0
        self._dead = False

    def get_stat_strings(
        self, stats, stat_format_spec="", val_format_spec="", delim="/"
    ):
        stats = [
            get_close_matches(stat, self._stat_list)[0] for stat in stats.split(delim)
        ]
        stat_vals = [str(self.stats[stat.lower().replace(" ", "_")]) for stat in stats]

        return (
            format(delim.join(stats), stat_format_spec),
            format(delim.join(stat_vals), val_format_spec),
        )

    def __str__(self):
        return f'{self.name}: {self.get_stat_strings("HP/Max HP")[1]} HP'

    def display_stats(self):
        print(
            stylize_text(f"{self.name}'s stats:", bold=True)
            + "\n    "
            + "\n    ".join(
                [
                    stylize_text(
                        f'{self.get_stat_strings(stat)[0] + ": ":<21}', bold=True
                    )
                    + f"{self.get_stat_strings(stat)[1]}"
                    for stat in self.stat_list
                ]
            )
        )

    def take_turn(self, combat):
        self.blocking = False

        if self.enraged > 0:
            self.enraged -= 1

        if not self.dead:
            possible_actions = ["Attack", "Block"] + (["Cast Spell"] if self.mana > 0 and self.spellbook else [])

            if not self.player:
                intent = secrets.choice(possible_actions)

            else:
                with output.use_tags('temp'):
                    print("\033[1mPossible Actions:\033[0m\n    " + '\n    '.join(possible_actions))
                    intent = get_close_matches(input('\nWhat action would you like to take?\n> '), possible_actions)[0]

                output.clear(False, 'temp')

            if intent == "Attack":
                if self.player:
                    with output.use_tags('temp'):
                        enemy_names = [enemy.name for enemy in combat.enemies if not enemy.dead]

                        print(
                            "\033[1mEnemies:\033[0m\n    "
                            + "\n    ".join(enemy_names)
                        )

                        self.do_attack(combat.enemies[enemy_names.index(get_close_matches(input('\nWho do you want to attack?\n> '), enemy_names)[0])])

                    output.clear(False, 'temp')

                else:
                    self.do_attack(combat.player)

            elif intent == "Block":
                print(f"{self.name} is blocking.")
                self.blocking = True

    def do_attack(self, other):
        if secrets.randbelow(max(other.stats["speed"] - self.stats["speed"], 4)) < 3:
            other.take_damage(
                int((self.stats["attack"] + secrets.randbelow(self.stats["attack"] // 2)) * (1 if not (self.player and self.player_class == "Berserker" and self.enraged > 0) else 1.5)), self
            )

        else:
            print(f"{other.name} dodged {self.name}'s attack!")

    def take_damage(self, damage, other):
        damage = max(
            damage
            - self.stats["passive_defense"]
            - (self.stats["block"] if self.blocking else 0),
            0,
        )
        damage = min(damage, self.stats["hp"])
        damage = damage if not (self.player and self.player_class == "Berserker" and self.enraged > 0) else damage // 2
        self.stats["hp"] -= damage

        print(f"{other.name} hit {self.name} for {damage} damage!")

        if self.player and self.player_class == "Berserker":
            self.enraged = 3

    def save(self, file_name=None):
        file_name = file_name if file_name and file_name.endswith(".save") else f"{self.name}.save"

        with ZipFile(file_name, 'w', compression=ZIP_LZMA) as archive:
            with archive.open("entity.info", "w") as infofile:
                for k in ["name", "player", "inventory", "_dead", "player_class"]:
                    infofile.write(f"{k}: {repr(self.__dict__[k])}\n")

            with archive.open("entity.stat", "w") as statfile:
                statfile.writelines([f"{k}: {repr(v)}" for k, v in self.stats.items()])

            archive.writestr('spells/temp.tmp', '')

            for i, spell_data in enumerate(zip(self.spellbook.items())):
                spell_data[1].save(f"spells/spell-{i}.spl", archive)

    @classmethod
    def load(cls, file_name=None):
        self = cls(from_file=True)

        if not (file_name and file_name.endswith(".save")):
            for root, dirs, files in os.walk("/content/"):
                for file in files:
                    if file.endswith(".save"):
                        file_name = os.path.join(root, file)
                        break

        with TemporaryDirectory() as temp:
            with ZipFile(file_name, "w", compression=ZIP_LZMA) as archive:
                ZipFile.extractall(temp)

            with open(os.path.join(temp, "entity.info"), "r") as infofile:
                for line in infofile.readlines():
                    k, v = line.strip("\n").split(": ")
                    self.__dict__[k] = eval(v)

            with open(os.path.join(temp, "entity.stat"), "r") as statfile:
                for line in statfile.readlines():
                    k, v = line.strip("\n").split(": ")
                    self.stats[k] = eval(v)

            spelldir = os.path.join(temp, "spells")

            if os.path.isdir(spelldir):
                for root, dirs, files in os.walk(spelldir):
                    for file in files:
                        self.spellbook.append(Spell.load(os.path.join(root, file)))

    # Some properties for easy accessing of stats
    @property
    def max_hp(self):
        return self.stats["max_hp"]

    @max_hp.setter
    def max_hp(self, value):
        self.stats["max_hp"] = value

    @property
    def hp(self):
        return self.stats["hp"]

    @hp.setter
    def hp(self, value):
        self.stats["hp"] = value

        if value <= 0:
            self.dead = True

    @property
    def attack(self):
        return self.stats["attack"]

    @attack.setter
    def attack(self, value):
        self.stats["attack"] = value

    @property
    def speed(self):
        return self.stats["speed"]

    @speed.setter
    def speed(self, value):
        self.stats["speed"] = value

    @property
    def block(self):
        return self.stats["block"]

    @block.setter
    def block(self, value):
        self.stats["block"] = value

    @property
    def passive_defense(self):
        return self.stats["passive_defense"]

    @passive_defense.setter
    def passive_defense(self, value):
        self.stats["passive_defense"] = value

    @property
    def magic_attack(self):
        return self.stats["magic_attack"]

    @magic_attack.setter
    def magic_attack(self, value):
        self.stats["magic_attack"] = value

    @property
    def magic_defense(self):
        return self.stats["magic_defense"]

    @magic_defense.setter
    def magic_defense(self, value):
        self.stats["magic_defense"] = value

    @property
    def mana(self):
        return self.stats["mana"]

    @mana.setter
    def mana(self, value):
        self.stats["current_mana"] += max(
            value - self.stats["mana"], -self.stats["current_mana"]
        )
        self.stats["mana"] = value

    @property
    def current_mana(self):
        return self.stats["current_mana"]

    @current_mana.setter
    def current_mana(self, value):
        self.stats["current_mana"] = value

    @property
    def dead(self):
        return self._dead

    @dead.setter
    def dead(self, value):
        if not isinstance(value, bool):
            raise TypeError(
                "The 'dead' property of 'Entity' objects must be a boolean value!"
            )

        if value and not self._dead:
            print(f"{self.name} has died!")

        if self._dead and not value:
            print(f"{self.name} has been resurrected!")

        self._dead = value


# Levelable entity class
class LevelableEntity(Entity):
    default_stats = {
        "level": 0,
        "exp": 0,
    }

    stat_list = [
        "Level",
        "EXP/EXP to Next",
        "HP/Max HP",
        "Attack",
        "Speed",
        "Block",
        "Passive Defense",
        "Magic Attack",
        "Magic Defense",
        "Mana",
    ]

    increasable_stats = [
        "Max HP",
        "Attack",
        "Speed",
        "Block",
        "Passive Defense",
        "Magic Attack",
        "Magic Defense",
        "Mana",
    ]

    def __init__(self, name="", spellbook={}, **kwargs):
        for k, v in LevelableEntity.default_stats.items():
            self.default_stats.setdefault(k, v)

        super().__init__(name, spellbook, **kwargs)

        self.update_level_req()

    def level_exp_func(self, level):
        return int(
            significant_digits(
                300 * 1.25 ** level,
                # Scale sig digs with the level a bit, but cap them at 5
                max(int(np.floor(np.log10(330 * (level + 1)))) - 1, 5),
            )
        )

    def update_level_req(self):
        self.exp_to_next = self.level_exp_func(self.level)

    def display_increasable_stats(self, increases=[0 for _ in increasable_stats]):
        print(
            stylize_text(f"{self.name}'s stats:", bold=True)
            + "\n    "
            + "\n    ".join(
                [
                    stylize_text(
                        f'{self.get_stat_strings(stat)[0] + ": ":<21}', bold=True
                    )
                    + f'{self.get_stat_strings(stat)[1]}{f" (+{increase})" if increase else ""}'
                    for stat, increase in zip(self.increasable_stats, increases)
                ]
            )
        )

    def prompt_stat_increase(self, points):
        stat_keys = [stat.lower().replace(" ", "_") for stat in self.increasable_stats]

        for _ in range(points):
            stat_to_increase = secrets.choice(stat_keys)
            self.increase_stat(stat_to_increase)

    def increase_stat(self, stat):
        if stat == "max_hp":
            self.stats["max_hp"] += 5
            self.stats["hp"] += 5

        else:
            self.stats[stat] += 1

    # Some properties for easy accessing of stats
    @property
    def level(self):
        return self.stats["level"]

    @level.setter
    def level(self, value):
        self.stats["level"] = value

    @property
    def exp(self):
        return self.stats["exp"]

    @exp.setter
    def exp(self, value):
        self.stats["exp"] = value

        if self.stats["exp"] >= self.exp_to_next:
            self.level += 1
            self.stats["exp"] -= self.exp_to_next

            self.update_level_req()
            print(
                "You leveled up! You now have two more stat increase points you can spend!"
            )
            self.prompt_stat_increase(2)

    @property
    def exp_to_next(self):
        return self.stats["exp_to_next"]

    @exp_to_next.setter
    def exp_to_next(self, value):
        self.stats["exp_to_next"] = value


# The class for the player
class Player(LevelableEntity):
    default_stats = {
        "max_hp": 20,
    }

    def __init__(self, *, from_file=False, **kwargs):
        for k, v in Player.default_stats.items():
            self.default_stats.setdefault(k, v)

        super().__init__(input("Enter your character's name:\n> "), **kwargs)

        self.player = True
        class_options = {
            "Warrior": tw.dedent("""\
            \033[1mStat Modifiers:\033[0m
                \033[1m+2\033[0m Attack
                \033[1m+1\033[0m Speed

            \033[1mSpecial Abilities:\033[0m
                No Special Abilities.
            """),
            "Berserker": tw.dedent("""\
            \033[1mStat Modifiers:\033[0m
                \033[1m+5\033[0m Max HP

            \033[1mSpecial Abilities:\033[0m
                \033[1mEnrage -\033[0m When taking damage, become \033[1mEnraged\033[0m for 3 turns. Being \033[1mEnraged\033[0m makes you take
                    \033[1m1/2\033[0m damage from physical attacks and deal \033[1m1.5x\033[0m damage with your own attacks.
            """),
            "Rogue": tw.dedent("""\
            \033[1mStat Modifiers:\033[0m
                \033[1m+3\033[0m Speed

            \033[1mSpecial Abilities:\033[0m
                No Special Abilities.
            """),
            # "Sorcerer",
            # "Wizard",
        }
        lower_options = [option.lower() for option in class_options]

        while True:
            selected = ""

            print(
                f"\033[H\033[2JBefore you start out on your journey, {self.name}, let's "
                "choose your character's class!\n\n\033[1mClasses:\n    "
                + "\n    ".join([k for k in class_options]) + "\033[0m\n"
            )

            try:
                selected = get_close_matches(input("Choose your class:\n> ").lower(), lower_options, cutoff=0.5)[0]

            except IndexError:
                while not selected:
                    selected = get_close_matches(input("\nThat wasn't close enough to any class to be able to guess what you meant!\nPlease try again. Choose your class:\n> ").lower(), lower_options, cutoff=0.5)[0]

            selected = [option for option in class_options][lower_options.index(selected)]

            print(f"\033[H\033[2J\033[1m{selected:^60}\n============================================================\033[0m\n{class_options[selected]}\n\033[1m============================================================\033[0m\n\nDo you want to choose \033[1m{selected}\033[0m as your class? (\033[1mY\033[0m/n)")

            if input("> ").lower() not in ["n", "no"]:
                self.player_class = selected
                break

        if self.player_class in ["Sorcerer", "Wizard"]:
            self.mana += 2

        if self.player_class == "Berserker":
            self.max_hp += 5
            self.enraged = 0

        if self.player_class == "Warrior":
            self.attack += 2
            self.speed += 1

        if self.player_class == "Rogue":
            self.speed += 3

        print(
            "\033[H\033[2JNow, let's get you a little stat boost to start off with!\n"
        )
        self.prompt_stat_increase(2)
        print(
            f"\033[H\033[2JCongratulations, {self.name}! You're now ready to begin "
            "your epic journey!"
        )

    def display_increasable_stats(
        self, increases=[0 for _ in LevelableEntity.increasable_stats]
    ):
        print(
            stylize_text("Your stats:", bold=True)
            + "\n    "
            + "\n    ".join(
                [
                    stylize_text(
                        f'{self.get_stat_strings(stat)[0] + ": ":<21}', bold=True
                    )
                    + f"{self.get_stat_strings(stat)[1]}"
                    + (f" (+{increase})" if increase else "")
                    for stat, increase in zip(self.increasable_stats, increases)
                ]
            )
        )

    def prompt_stat_increase(self, points):
        lower_stats = [stat.lower() for stat in self.increasable_stats]
        stat_increases = [0 for _ in lower_stats]

        for used in range(points):
            confirm = False

            print("\033[H\033[2JYou can now increase your stats!\n")
            self.display_increasable_stats(stat_increases)

            while not confirm:
                try:
                    stat_to_increase = get_close_matches(
                        input(
                            f"\nChoose which stat you'd like to increase now! (Points remaining: {points - used})\n> "
                        ).lower(),
                        lower_stats,
                        cutoff=0.4,
                    )[0]

                except IndexError:
                    while True:
                        try:
                            stat_to_increase = get_close_matches(
                                input(
                                    f"\nThat wasn't close enough to any stats to be able to guess what you meant!\nPlease try again. Choose which stat you'd like to increase now! (Points remaining: {points - used})\n> "
                                ).lower(),
                                lower_stats,
                                cutoff=0.4,
                            )[0]
                            break

                        except IndexError:
                            continue

                stat_to_increase = self.increasable_stats[
                    lower_stats.index(stat_to_increase)
                ]
                confirm = input(f"You're going to increase your {stylize_text(stat_to_increase, bold=True)} by \033[1m+{5 if stat_to_increase == 'Max HP' else 1}\033[0m. Is this correct? (\033[1mY\033[0m/n)\n> ").lower() not in ["n", "no"]

            self.increase_stat(stat_to_increase.lower().replace(" ", "_"))
            stat_increases[self.increasable_stats.index(stat_to_increase)] += (
                5 if stat_to_increase == "Max HP" else 1
            )
