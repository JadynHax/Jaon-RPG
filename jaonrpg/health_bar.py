from .utils import stylize_text

# Health bar class
class HealthBar(object):
    bar_chars = ["  ", "▏", "▎", "▍", "█", "▋", "▊", "▉", "██"]

    def __init__(
        self,
        entity,
        width,
        *,
        align="left",
        bright_bar=False,
        bar_color="default",
        bright_bar_back=False,
        bar_back_color="default",
    ):
        odd_length_bar = bool(
            (width - len(f"{entity.name}{entity.hp}{entity.max_hp}")) % 2
        )
        self.entity = entity
        self.width = width
        self.bar_color = bar_color
        self.bright_bar = bright_bar
        self.bar_back_color = bar_back_color
        self.bright_bar_back = bright_bar_back
        self.bar_format_str = (
            f'▐{{bar}}▌{" " if odd_length_bar else ""} ({entity.hp}/{entity.max_hp} HP) - {entity.name}'
            if align == "right"
            else f'{entity.name} - ({entity.hp}/{entity.max_hp} HP) {" " if odd_length_bar else ""}▐{{bar}}▌'
            if align == "left"
            else "▐{bar}▌"
        )
        self.bar_available_width = (
            width - len(self.bar_format_str.replace("{bar}", ""))
        ) // 2

        if self.bar_available_width <= 0:
            raise ValueError("Width is too small for bar!")

        self.bar_format_str = self.bar_format_str.replace(
            entity.name, stylize_text(entity.name, bold=True)
        )

    def __repr__(self):
        hp_ratio = self.entity.hp / self.entity.max_hp
        full_blocks, frac_block = divmod(
            int(hp_ratio * self.bar_available_width * 8), 8
        )

        bar = "██" * full_blocks + (
            self.bar_chars[frac_block]
            + "  " * (self.bar_available_width - full_blocks - 1)
            if full_blocks < self.bar_available_width
            else ""
        )

        return self.bar_format_str.format(
            bar=stylize_text(
                bar,
                bright_text=self.bright_bar,
                bright_background=self.bright_bar_back,
                text_color=self.bar_color,
                background_color=self.bar_back_color,
            )
        )

    def __str__(self):
        return repr(self)
