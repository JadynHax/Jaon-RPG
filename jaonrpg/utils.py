import numpy as np

__all__ = ["significant_digits", "stylize_text"]


# A function to round a number to "precision" significant digits
def significant_digits(n, precision=1):
    places = -int(np.floor(np.log10(abs(n)))) + (precision - 1)

    return int(round(n, places)) if places <= 0 else round(n, places)


# Stylize text with ANSI escape codes based on keyword arguments
def stylize_text(
    text,
    bold=False,
    underline=False,
    conceal=False,
    strikethrough=False,
    bright_text=False,
    bright_background=False,
    text_color="default",
    background_color="default",
):
    colors = {
        "black": "0",
        "red": "1",
        "green": "2",
        "yellow": "3",
        "blue": "4",
        "magenta": "5",
        "cyan": "6",
        "white": "7",
        "default": "9",
    }

    if text_color not in colors and not (
        text_color.startswith("8;5;") or text_color.startswith("8;2;")
    ):
        raise ValueError(
            f"{text_color} is not a color that can be printed with ANSI escapes!"
        )

    if background_color not in colors and not (
        background_color.startswith("8;5;") or background_color.startswith("8;2;")
    ):
        raise ValueError(
            f"{background_color} is not a color that can be printed with ANSI escapes!"
        )

    ansi_args_list = []

    text_color = (
        "3"
        if (text_color == "default") or text_color.startswith("8") or not bright_text
        else "9"
    ) + (text_color if text_color.startswith("8") else colors[text_color])
    background_color = (
        "4"
        if (background_color == "default")
        or background_color.startswith("8")
        or not bright_background
        else "10"
    ) + (
        background_color
        if background_color.startswith("8")
        else colors[background_color]
    )

    if bold:
        ansi_args_list.append("1")

    if underline:
        ansi_args_list.append("4")

    if conceal:
        ansi_args_list.append("8")

    if strikethrough:
        ansi_args_list.append("9")

    ansi_args_list.append(text_color)
    ansi_args_list.append(background_color)

    return "\033[" + ";".join(ansi_args_list) + "m" + text + "\033[0m"
